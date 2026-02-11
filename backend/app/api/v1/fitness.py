"""
Shortlist — Resume Fitness Scoring Endpoints

POST /api/v1/fitness/score    — Score resume against a JD analysis
GET  /api/v1/fitness/{id}     — Retrieve a saved fitness evaluation
GET  /api/v1/fitness/         — List user's fitness evaluations
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.schemas.fitness import (
    FitnessScoreRequest,
    FitnessScoreResponse,
    MatchedSkill,
    MissingSkill,
    Improvement,
)
from app.agents.orchestrator import compile_fitness_pipeline
from app.services.db_service import (
    get_jd_analysis,
    create_fitness_score,
    update_fitness_score,
    get_fitness_score,
    list_fitness_scores,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.fitness")


def _safe_parse_fitness(raw: dict, analysis: dict, fitness_id: str, elapsed_ms: int) -> FitnessScoreResponse:
    """Safely parse raw fitness result into a validated response."""
    matched = []
    for m in raw.get("matched_skills", []):
        try:
            matched.append(MatchedSkill(name=m["name"], evidence=m.get("evidence", "")[:300]))
        except Exception:
            continue

    missing = []
    for m in raw.get("missing_skills", []):
        try:
            missing.append(MissingSkill(
                name=m["name"],
                importance=m.get("importance", "important"),
                suggestion=m.get("suggestion", "")[:500],
            ))
        except Exception:
            continue

    improvements = []
    for imp in raw.get("improvements", []):
        try:
            improvements.append(Improvement(
                area=imp["area"],
                current_state=imp.get("current_state", "")[:500],
                recommended_action=imp.get("recommended_action", imp.get("suggestion", ""))[:500],
                impact=imp.get("impact", imp.get("priority", "medium")),
            ))
        except Exception:
            continue

    return FitnessScoreResponse(
        id=fitness_id,
        analysis_id=analysis["id"],
        fitness_score=max(0, min(100, float(raw.get("fitness_score", 0)))),
        verdict=raw.get("verdict", "weak_fit"),
        matched_skills=matched,
        missing_skills=missing,
        strengths=raw.get("strengths", [])[:10],
        improvements=improvements,
        detailed_feedback=str(raw.get("detailed_feedback", ""))[:5000],
        role=analysis.get("role", "Unknown"),
        company_type=analysis.get("company_type", "mid_level"),
        processing_time_ms=elapsed_ms,
    )


@router.post(
    "/score",
    response_model=FitnessScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score Resume Against JD",
    description="Evaluates how well a resume matches a JD analysis, with actionable feedback.",
)
async def score_fitness(
    request: FitnessScoreRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Fetch the JD analysis
    2. Create pending fitness record
    3. Run fitness pipeline
    4. Persist and return results
    """
    logger.info(f"Fitness scoring requested by user {user.user_id} for analysis {request.analysis_id}")
    start_time = time.time()

    # Step 1: Fetch JD analysis
    analysis = await get_jd_analysis(request.analysis_id, user.user_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD analysis not found",
        )
    if analysis.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed (status: {analysis.get('status')})",
        )

    # Step 2: Create pending record
    try:
        record = await create_fitness_score(
            user_id=user.user_id,
            analysis_id=request.analysis_id,
            resume_text=request.resume_text,
        )
        fitness_id = record["id"]
    except Exception as e:
        logger.error(f"Failed to create fitness record: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize fitness evaluation.",
        )

    # Step 3: Run fitness pipeline
    try:
        pipeline = compile_fitness_pipeline()
        initial_state = {
            "jd_text": analysis.get("jd_text", ""),
            "role": analysis["role"],
            "company_type": analysis["company_type"],
            "geography": analysis.get("geography"),
            "skill_profile": analysis.get("skill_profile", {}),
            "company_modifiers": analysis.get("company_modifiers", {}),
            "resume_text": request.resume_text,
            "user_id": user.user_id,
            "analysis_id": request.analysis_id,
            "messages": [],
            "errors": [],
        }

        final_state = await pipeline.ainvoke(initial_state)

        errors = final_state.get("errors", [])
        if errors:
            elapsed_ms = int((time.time() - start_time) * 1000)
            await update_fitness_score(
                fitness_id, user.user_id,
                status="failed",
                error_message="; ".join(errors),
                processing_time_ms=elapsed_ms,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fitness evaluation could not be completed. Please try again.",
            )

        fitness_result = final_state.get("fitness_result")
        if not fitness_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fitness evaluation produced no result.",
            )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        await update_fitness_score(
            fitness_id, user.user_id,
            status="failed",
            error_message=str(e),
            processing_time_ms=elapsed_ms,
        )
        logger.error(f"Fitness pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fitness evaluation encountered an error.",
        )

    # Step 4: Persist results
    elapsed_ms = int((time.time() - start_time) * 1000)
    await update_fitness_score(
        fitness_id, user.user_id,
        fitness_score=fitness_result.get("fitness_score"),
        verdict=fitness_result.get("verdict"),
        matched_skills=fitness_result.get("matched_skills"),
        missing_skills=fitness_result.get("missing_skills"),
        strengths=fitness_result.get("strengths"),
        improvements=fitness_result.get("improvements"),
        detailed_feedback=fitness_result.get("detailed_feedback"),
        status="completed",
        processing_time_ms=elapsed_ms,
    )

    logger.info(f"Fitness score {fitness_id} completed in {elapsed_ms}ms")

    return _safe_parse_fitness(fitness_result, analysis, fitness_id, elapsed_ms)


@router.get(
    "/{fitness_id}",
    response_model=FitnessScoreResponse,
    summary="Get a fitness evaluation",
)
async def get_fitness(
    fitness_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve a previously saved fitness evaluation."""
    record = await get_fitness_score(fitness_id, user.user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fitness evaluation not found")

    # Get the parent analysis for role/company info
    analysis = await get_jd_analysis(record["analysis_id"], user.user_id)
    role = analysis["role"] if analysis else "Unknown"
    company_type = analysis["company_type"] if analysis else "mid_level"

    return FitnessScoreResponse(
        id=record["id"],
        analysis_id=record["analysis_id"],
        fitness_score=record.get("fitness_score") or 0,
        verdict=record.get("verdict") or "weak_fit",
        matched_skills=[MatchedSkill(**m) for m in (record.get("matched_skills") or [])],
        missing_skills=[MissingSkill(**m) for m in (record.get("missing_skills") or [])],
        strengths=record.get("strengths") or [],
        improvements=[
            Improvement(
                area=i.get("area", ""),
                current_state=i.get("current_state", "") or "",
                recommended_action=i.get("recommended_action", "") or i.get("suggestion", "") or "",
                impact=i.get("impact", "") or i.get("priority", "medium") or "medium",
            )
            for i in (record.get("improvements") or [])
        ],
        detailed_feedback=record.get("detailed_feedback") or "",
        role=role,
        company_type=company_type,
        processing_time_ms=record.get("processing_time_ms") or 0,
    )


@router.get(
    "/",
    summary="List fitness evaluations",
)
async def list_fitness(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all fitness evaluations for the authenticated user."""
    scores, total = await list_fitness_scores(user.user_id, limit, offset)
    return {"scores": scores, "total": total, "limit": limit, "offset": offset}
