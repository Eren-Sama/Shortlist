"""
Shortlist — Portfolio Optimizer Endpoints

POST /api/v1/portfolio/optimize — Generate portfolio materials
GET  /api/v1/portfolio/{id}     — Fetch a single result
GET  /api/v1/portfolio/         — List all portfolio outputs
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.agents.orchestrator import compile_portfolio_pipeline
from app.schemas.portfolio import PortfolioOptimizeRequest, PortfolioOptimizeResponse
from app.services.db_service import (
    create_portfolio_output,
    update_portfolio_output,
    get_portfolio_output,
    list_portfolio_outputs,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.portfolio")


@router.post(
    "/optimize",
    response_model=PortfolioOptimizeResponse,
    summary="Optimize Portfolio Materials",
    description="Generates polished README, ATS resume bullets, demo script, and LinkedIn post.",
)
async def optimize_portfolio(
    request: PortfolioOptimizeRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    logger.info(
        f"Portfolio optimization requested by user {user.user_id} "
        f"for project: {request.project_title}"
    )

    start_time = time.time()

    # Create DB record
    try:
        record = await create_portfolio_output(
            user_id=user.user_id,
            project_title=request.project_title,
            project_description=request.project_description,
            tech_stack=request.tech_stack,
            target_role=request.target_role,
            analysis_id=request.analysis_id,
        )
        portfolio_id = record["id"]
    except Exception as e:
        logger.error(f"Failed to create portfolio record: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize portfolio generation. Please try again.",
        )

    # Run pipeline
    try:
        pipeline = compile_portfolio_pipeline()
        initial_state = {
            "portfolio_project_title": request.project_title,
            "portfolio_project_description": request.project_description,
            "portfolio_tech_stack": request.tech_stack,
            "portfolio_key_features": request.key_features,
            "portfolio_repo_score": request.repo_score,
            "portfolio_target_role": request.target_role,
            "messages": [],
            "user_id": user.user_id,
            "analysis_id": request.analysis_id,
        }

        result = await pipeline.ainvoke(initial_state)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Check for errors
        errors = result.get("errors", [])
        if errors or result.get("current_phase") == "portfolio_error":
            error_msg = "; ".join(errors) if errors else "Portfolio generation failed"
            await update_portfolio_output(
                portfolio_id,
                user.user_id,
                status="failed",
                error_message=error_msg,
                processing_time_ms=elapsed_ms,
            )
            logger.warning(f"Portfolio {portfolio_id} failed: {error_msg[:200]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Portfolio generation could not be completed. Please try again.",
            )

        # Extract portfolio output
        output = result.get("portfolio_output", {})
        if not output:
            await update_portfolio_output(
                portfolio_id,
                user.user_id,
                status="failed",
                error_message="Empty portfolio output",
                processing_time_ms=elapsed_ms,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Portfolio generation returned empty output. Please try again.",
            )

        # Persist results
        await update_portfolio_output(
            portfolio_id,
            user.user_id,
            readme_markdown=output.get("readme_markdown", ""),
            resume_bullets=output.get("resume_bullets", []),
            demo_script=output.get("demo_script", {}),
            linkedin_post=output.get("linkedin_post", {}),
            status="completed",
            processing_time_ms=elapsed_ms,
        )

        logger.info(f"Portfolio {portfolio_id} completed in {elapsed_ms}ms")

        return PortfolioOptimizeResponse(
            readme_markdown=output.get("readme_markdown", ""),
            resume_bullets=output.get("resume_bullets", []),
            demo_script=output.get("demo_script", {}),
            linkedin_post=output.get("linkedin_post", {}),
            generation_metadata={
                "portfolio_id": portfolio_id,
                "processing_time_ms": elapsed_ms,
                "model": "llama-3.3-70b-versatile",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Portfolio generation error: {e}", exc_info=True)
        await update_portfolio_output(
            portfolio_id,
            user.user_id,
            status="failed",
            error_message=str(e)[:1000],
            processing_time_ms=elapsed_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Portfolio generation encountered an error. Please try again.",
        )


@router.get(
    "/{portfolio_id}",
    summary="Get Portfolio Output",
    description="Fetch a single portfolio output by ID.",
)
async def get_portfolio(
    portfolio_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    record = await get_portfolio_output(portfolio_id, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio output not found",
        )
    return record


@router.get(
    "/",
    summary="List Portfolio Outputs",
    description="List all portfolio outputs for the authenticated user.",
)
async def list_portfolios(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    records, total = await list_portfolio_outputs(
        user.user_id, limit=limit, offset=offset,
    )
    return {
        "items": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
