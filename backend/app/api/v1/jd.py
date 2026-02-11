"""
Shortlist — JD Analysis Endpoints

POST /api/v1/jd/analyze     — Analyze a job description
GET  /api/v1/jd/{id}        — Retrieve a saved analysis
GET  /api/v1/jd/            — List user's analyses
"""

import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.schemas.jd import (
    JDAnalysisRequest,
    JDAnalysisResponse,
    SkillProfile,
    CompanyModifiers,
    Skill,
    EngineeringExpectation,
)
from app.agents.orchestrator import compile_jd_pipeline
from app.services.db_service import (
    create_jd_analysis,
    update_jd_analysis,
    get_jd_analysis,
    list_jd_analyses,
    delete_jd_analysis,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.jd")


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from a string."""
    import re
    text = text.strip()
    # Remove leading ```json or ``` (any language tag)
    text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
    # Remove trailing ```
    text = re.sub(r'```\s*$', '', text)
    return text.strip()


def _try_extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from text that may have markdown fences or extra text."""
    if not isinstance(text, str) or len(text) < 10:
        return None
    # First, strip markdown fences
    clean = _strip_markdown_fences(text)
    # Try to find a JSON object in the text
    brace_start = clean.find("{")
    if brace_start == -1:
        return None
    # Find the matching closing brace from the end
    brace_end = clean.rfind("}")
    if brace_end <= brace_start:
        return None
    candidate = clean[brace_start:brace_end + 1]
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _safe_parse_skill_profile(raw) -> SkillProfile:
    """Safely parse a raw skill_profile (dict, JSON string, or fallback with
    JSON embedded in summary) into a validated SkillProfile."""
    # Handle string input
    if isinstance(raw, str):
        parsed = _try_extract_json(raw)
        raw = parsed if parsed else {}
    if not isinstance(raw, dict):
        raw = {}

    # Detect the jd_node fallback case: skills is empty but summary contains
    # the actual JSON from the LLM response (happens when markdown stripping
    # failed during analysis).
    if not raw.get("skills") and isinstance(raw.get("summary"), str):
        embedded = _try_extract_json(raw["summary"])
        if embedded and isinstance(embedded.get("skills"), list) and len(embedded["skills"]) > 0:
            logger.info("Re-extracted skill_profile from embedded JSON in summary field")
            raw = embedded

    skills = []
    for s in raw.get("skills", []):
        try:
            skills.append(Skill(
                name=s.get("name", "Unknown"),
                category=s.get("category", "concept"),
                weight=float(s.get("weight", 5.0)),
                source=s.get("source", "inferred"),
            ))
        except Exception:
            continue

    expectations = []
    for e in raw.get("engineering_expectations", []):
        try:
            expectations.append(EngineeringExpectation(
                dimension=e.get("dimension", "Unknown"),
                importance=float(e.get("importance", 5.0)),
                description=e.get("description", ""),
            ))
        except Exception:
            continue

    return SkillProfile(
        skills=skills,
        experience_level=raw.get("experience_level", "mid"),
        domain=raw.get("domain", "Software Engineering"),
        engineering_expectations=expectations,
        key_responsibilities=raw.get("key_responsibilities", []),
        summary=raw.get("summary", "Analysis complete.")[:8000],
    )


def _safe_parse_company_modifiers(raw) -> CompanyModifiers:
    """Safely parse company_modifiers (dict or JSON string) into a validated CompanyModifiers."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return CompanyModifiers(
        company_type=raw.get("company_type", "mid_level"),
        emphasis_areas=raw.get("emphasis_areas", []),
        weight_adjustments=raw.get("weight_adjustments", {}),
        portfolio_focus=raw.get("portfolio_focus", ""),
    )


@router.post(
    "/analyze",
    response_model=JDAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a Job Description",
    description="Extracts skill profile, engineering expectations, and company-type modifiers from a JD.",
)
async def analyze_jd(
    request: JDAnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Create a pending record in Supabase
    2. Run JD through LangGraph agent pipeline
    3. Update record with results
    4. Return structured analysis
    """
    logger.info(f"JD analysis requested by user {user.user_id} for role: {request.role}")
    start_time = time.time()

    # Step 1: Create a pending DB record
    try:
        record = await create_jd_analysis(
            user_id=user.user_id,
            jd_text=request.jd_text,
            role=request.role,
            company_type=request.company_type.value,
            geography=request.geography,
        )
        analysis_id = record["id"]
    except Exception as e:
        logger.error(f"Failed to create JD analysis record: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize analysis. Please try again.",
        )

    # Step 2: Mark as processing
    await update_jd_analysis(analysis_id, user.user_id, status="processing")

    # Step 3: Run the LangGraph JD pipeline
    try:
        pipeline = compile_jd_pipeline()
        initial_state = {
            "jd_text": request.jd_text,
            "role": request.role,
            "company_type": request.company_type.value,
            "geography": request.geography,
            "user_id": user.user_id,
            "analysis_id": analysis_id,
            "messages": [],
            "errors": [],
        }

        final_state = await pipeline.ainvoke(initial_state)

        # Check for pipeline errors
        errors = final_state.get("errors", [])
        if errors:
            elapsed_ms = int((time.time() - start_time) * 1000)
            await update_jd_analysis(
                analysis_id,
                user.user_id,
                status="failed",
                error_message="; ".join(errors),
                processing_time_ms=elapsed_ms,
            )
            logger.warning(f"JD analysis {analysis_id} failed: {errors[0]}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Analysis could not be completed. Please refine your input and try again.",
            )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        await update_jd_analysis(
            analysis_id,
            user.user_id,
            status="failed",
            error_message=str(e),
            processing_time_ms=elapsed_ms,
        )
        logger.error(f"JD pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis pipeline encountered an error. Please try again.",
        )

    # Step 4: Persist results
    elapsed_ms = int((time.time() - start_time) * 1000)
    skill_profile_raw = final_state.get("skill_profile", {})
    company_modifiers_raw = final_state.get("company_modifiers", {})

    await update_jd_analysis(
        analysis_id,
        user.user_id,
        skill_profile=skill_profile_raw,
        engineering_expectations=final_state.get("engineering_expectations"),
        company_modifiers=company_modifiers_raw,
        status="completed",
        processing_time_ms=elapsed_ms,
    )

    # Step 5: Return structured response
    skill_profile = _safe_parse_skill_profile(skill_profile_raw)
    company_modifiers = _safe_parse_company_modifiers(company_modifiers_raw)

    logger.info(
        f"JD analysis {analysis_id} completed in {elapsed_ms}ms — "
        f"{len(skill_profile.skills)} skills extracted"
    )

    return JDAnalysisResponse(
        analysis_id=analysis_id,
        skill_profile=skill_profile,
        company_modifiers=company_modifiers,
        raw_role=request.role,
        raw_company_type=request.company_type,
        raw_geography=request.geography,
    )


@router.get(
    "/{analysis_id}",
    response_model=JDAnalysisResponse,
    summary="Get a saved JD analysis",
)
async def get_analysis(
    analysis_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve a previously saved JD analysis by ID."""
    logger.info(f"Fetching analysis {analysis_id} for user {user.user_id}")

    record = await get_jd_analysis(analysis_id, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    skill_profile = _safe_parse_skill_profile(record.get("skill_profile") or {})
    company_modifiers = _safe_parse_company_modifiers(record.get("company_modifiers") or {})

    return JDAnalysisResponse(
        analysis_id=record["id"],
        skill_profile=skill_profile,
        company_modifiers=company_modifiers,
        raw_role=record["role"],
        raw_company_type=record["company_type"],
        raw_geography=record.get("geography"),
    )


@router.get(
    "/",
    summary="List user's JD analyses",
)
async def list_analyses(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all JD analyses for the authenticated user."""
    logger.info(f"Listing analyses for user {user.user_id}")

    analyses, total = await list_jd_analyses(user.user_id, limit, offset)

    return {
        "analyses": analyses,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete(
    "/{analysis_id}",
    summary="Delete a JD analysis",
    status_code=status.HTTP_200_OK,
)
async def delete_analysis(
    analysis_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a JD analysis and all related records (capstones, fitness scores, etc.)."""
    logger.info(f"Deleting analysis {analysis_id} for user {user.user_id}")

    deleted = await delete_jd_analysis(analysis_id, user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    return {"deleted": True, "analysis_id": analysis_id}
