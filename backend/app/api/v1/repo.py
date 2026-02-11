"""
Shortlist — Repo Analyzer Endpoints

POST /api/v1/repo/analyze — Analyze a GitHub repository
GET  /api/v1/repo/{id}    — Get a saved analysis
GET  /api/v1/repo/        — List user's repo analyses
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.schemas.repo import (
    RepoAnalysisRequest,
    RepoAnalysisResponse,
    RepoScoreCard,
    ScoreDimension,
)
from app.agents.orchestrator import compile_repo_pipeline
from app.services.db_service import (
    create_repo_analysis,
    update_repo_analysis,
    get_repo_analysis,
    list_repo_analyses,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.repo")


def _safe_parse_dimension(raw: dict, name: str) -> ScoreDimension:
    """Safely parse a score dimension from raw scorecard dict."""
    return ScoreDimension(
        name=name,
        score=float(raw.get("score", 5.0)),
        details=raw.get("details", "")[:1000],
        suggestions=raw.get("suggestions", [])[:5],
    )


def _safe_parse_scorecard(raw: dict, github_url: str) -> RepoScoreCard:
    """Safely parse raw scorecard dict into validated RepoScoreCard."""
    return RepoScoreCard(
        repo_url=raw.get("repo_url", github_url),
        repo_name=raw.get("repo_name", github_url.split("/")[-1]),
        primary_language=raw.get("primary_language"),
        total_files=raw.get("total_files", 0),
        total_lines=raw.get("total_lines", 0),
        code_quality=_safe_parse_dimension(
            raw.get("code_quality", {}), "Code Quality"
        ),
        test_coverage=_safe_parse_dimension(
            raw.get("test_coverage", {}), "Test Coverage"
        ),
        complexity=_safe_parse_dimension(
            raw.get("complexity", {}), "Complexity"
        ),
        structure=_safe_parse_dimension(
            raw.get("structure", {}), "Structure"
        ),
        deployment_readiness=_safe_parse_dimension(
            raw.get("deployment_readiness", {}), "Deployment Readiness"
        ),
        overall_score=float(raw.get("overall_score", 5.0)),
        summary=raw.get("summary", "Analysis complete.")[:2000],
        top_improvements=raw.get("top_improvements", [])[:10],
    )


@router.post(
    "/analyze",
    response_model=RepoAnalysisResponse,
    summary="Analyze a GitHub Repository",
    description="Analyzes repository structure, code quality, and generates a recruiter scorecard.",
)
async def analyze_repo(
    request: RepoAnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Create a pending record in Supabase
    2. Run repo through LangGraph analysis pipeline
    3. Update record with scorecard results
    4. Return structured response
    """
    logger.info(
        f"Repo analysis requested by user {user.user_id} "
        f"for {request.github_url}"
    )
    start_time = time.time()

    # Step 1: Create pending DB record
    try:
        record = await create_repo_analysis(
            user_id=user.user_id,
            github_url=request.github_url,
        )
        analysis_id = record["id"]
    except Exception as e:
        logger.error(f"Failed to create repo analysis record: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize analysis. Please try again.",
        )

    # Step 2: Mark as processing
    await update_repo_analysis(analysis_id, user.user_id, status="processing")

    # Step 3: Run the LangGraph repo pipeline
    try:
        pipeline = compile_repo_pipeline()
        initial_state = {
            "repo_url": request.github_url,
            "user_id": user.user_id,
            "analysis_id": analysis_id,
            "jd_text": "",  # Not used in repo pipeline
            "role": "",
            "company_type": "",
            "messages": [],
            "errors": [],
        }

        final_state = await pipeline.ainvoke(initial_state)

        # Check for pipeline errors
        errors = final_state.get("errors", [])
        if errors:
            elapsed_ms = int((time.time() - start_time) * 1000)
            await update_repo_analysis(
                analysis_id,
                user.user_id,
                status="failed",
                error_message="; ".join(errors),
                processing_time_ms=elapsed_ms,
            )
            logger.warning(f"Repo analysis {analysis_id} failed: {errors[0]}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Repository analysis could not be completed. Please check the URL and try again.",
            )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        await update_repo_analysis(
            analysis_id,
            user.user_id,
            status="failed",
            error_message=str(e),
            processing_time_ms=elapsed_ms,
        )
        logger.error(f"Repo pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis pipeline encountered an error. Please try again.",
        )

    # Step 4: Persist results
    elapsed_ms = int((time.time() - start_time) * 1000)
    scorecard_raw = final_state.get("repo_scorecard", {})

    await update_repo_analysis(
        analysis_id,
        user.user_id,
        scorecard=scorecard_raw,
        repo_name=scorecard_raw.get("repo_name"),
        primary_language=scorecard_raw.get("primary_language"),
        status="completed",
        processing_time_ms=elapsed_ms,
    )

    # Step 5: Return structured response
    scorecard = _safe_parse_scorecard(scorecard_raw, request.github_url)

    logger.info(
        f"Repo analysis {analysis_id} completed in {elapsed_ms}ms — "
        f"Score: {scorecard.overall_score}/10"
    )

    return RepoAnalysisResponse(
        analysis_id=analysis_id,
        scorecard=scorecard,
        analysis_metadata={
            "processing_time_ms": elapsed_ms,
            "github_url": request.github_url,
        },
    )


@router.get(
    "/{analysis_id}",
    response_model=RepoAnalysisResponse,
    summary="Get a saved repo analysis",
)
async def get_analysis(
    analysis_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve a previously saved repo analysis by ID."""
    logger.info(f"Fetching repo analysis {analysis_id} for user {user.user_id}")

    record = await get_repo_analysis(analysis_id, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    scorecard = _safe_parse_scorecard(
        record.get("scorecard") or {},
        record["github_url"],
    )

    return RepoAnalysisResponse(
        analysis_id=record["id"],
        scorecard=scorecard,
        analysis_metadata={
            "processing_time_ms": record.get("processing_time_ms"),
            "github_url": record["github_url"],
            "status": record["status"],
        },
    )


@router.get(
    "/",
    summary="List user's repo analyses",
)
async def list_analyses(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all repo analyses for the authenticated user."""
    logger.info(f"Listing repo analyses for user {user.user_id}")

    analyses, total = await list_repo_analyses(user.user_id, limit, offset)

    # Extract overall_score from scorecard JSONB and strip the blob
    items = []
    for a in analyses:
        scorecard = a.pop("scorecard", None) or {}
        a["overall_score"] = float(scorecard.get("overall_score", 0))
        items.append(a)

    return {
        "analyses": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
