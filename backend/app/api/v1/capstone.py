"""
Shortlist — Capstone Generator Endpoints

POST /api/v1/capstone/generate         — Generate tailored project ideas
GET  /api/v1/capstone/{analysis_id}    — Get projects for an analysis
PUT  /api/v1/capstone/{project_id}/select — Toggle project selection
"""

import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.schemas.capstone import CapstoneGenerationRequest, CapstoneGenerationResponse, ProjectIdea, ArchitectureOverview
from app.agents.orchestrator import compile_jd_pipeline
from app.services.db_service import (
    get_jd_analysis,
    create_capstone_projects,
    get_capstone_projects,
    toggle_capstone_selected,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.capstone")


def _safe_parse_project(raw: dict) -> ProjectIdea:
    """Safely parse a raw dict into a validated ProjectIdea model."""
    arch_raw = raw.get("architecture", {})
    if isinstance(arch_raw, str):
        architecture = ArchitectureOverview(
            description=arch_raw[:2000],
            components=[],
            data_flow="See description",
        )
    elif isinstance(arch_raw, dict):
        architecture = ArchitectureOverview(
            description=arch_raw.get("description", "")[:2000],
            components=arch_raw.get("components", []),
            data_flow=arch_raw.get("data_flow", "")[:1000],
            diagram_mermaid=arch_raw.get("diagram_mermaid"),
        )
    else:
        architecture = ArchitectureOverview(
            description="Architecture details not available",
            components=[],
            data_flow="N/A",
        )

    return ProjectIdea(
        title=raw.get("title", "Untitled Project")[:200],
        problem_statement=raw.get("problem_statement", "")[:1500],
        recruiter_match_reasoning=raw.get("recruiter_match_reasoning", "")[:1000],
        architecture=architecture,
        tech_stack=raw.get("tech_stack", []),
        complexity_level=max(1, min(5, int(raw.get("complexity_level", 3)))),
        estimated_days=max(1, min(90, int(raw.get("estimated_days", 14)))),
        resume_bullet=raw.get("resume_bullet", "")[:300],
        key_features=raw.get("key_features", []),
        differentiator=raw.get("differentiator", "")[:500],
    )


@router.post(
    "/generate",
    response_model=CapstoneGenerationResponse,
    summary="Generate Capstone Project Ideas",
    description="Produces tailored capstone project ideas based on a JD analysis.",
)
async def generate_capstone_projects(
    request: CapstoneGenerationRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Fetch the JD analysis record
    2. Re-run the pipeline from the saved skill_profile → capstone node
    3. Persist generated projects
    4. Return structured response
    """
    logger.info(
        f"Capstone generation requested by user {user.user_id} "
        f"for analysis {request.analysis_id}"
    )
    start_time = time.time()

    # Step 1: Fetch the parent JD analysis
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

    # Step 2: Run the full JD pipeline (JD → Company → Capstone)
    # We supply the original JD so the pipeline can produce capstone projects
    try:
        pipeline = compile_jd_pipeline()
        initial_state = {
            "jd_text": analysis["jd_text"],
            "role": analysis["role"],
            "company_type": analysis["company_type"],
            "geography": analysis.get("geography"),
            "user_id": user.user_id,
            "analysis_id": request.analysis_id,
            "messages": [],
            "errors": [],
        }

        final_state = await pipeline.ainvoke(initial_state)

        errors = final_state.get("errors", [])
        if errors:
            logger.warning(f"Capstone generation failed: {errors[0][:200]}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project generation could not be completed. Please try again.",
            )

        raw_projects = final_state.get("generated_projects", [])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Capstone pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Capstone generation encountered an error. Please try again.",
        )

    # Step 3: Persist to database
    try:
        db_projects = await create_capstone_projects(
            user_id=user.user_id,
            analysis_id=request.analysis_id,
            projects=raw_projects,
        )
    except Exception as e:
        logger.error(f"Failed to persist capstone projects: {e}", exc_info=True)
        # Still return the generated projects even if DB save fails
        db_projects = None

    # Step 4: Parse and return
    elapsed_ms = int((time.time() - start_time) * 1000)
    parsed_projects = []
    for p in raw_projects:
        try:
            parsed_projects.append(_safe_parse_project(p))
        except Exception as e:
            logger.warning(f"Failed to parse project: {e}")
            continue

    logger.info(
        f"Capstone generation completed in {elapsed_ms}ms — "
        f"{len(parsed_projects)} projects generated"
    )

    return CapstoneGenerationResponse(
        analysis_id=request.analysis_id,
        projects=parsed_projects,
        generation_metadata={
            "processing_time_ms": elapsed_ms,
            "projects_generated": len(parsed_projects),
            "projects_persisted": len(db_projects) if db_projects else 0,
        },
    )


@router.get(
    "/{analysis_id}",
    summary="Get capstone projects for an analysis",
)
async def get_projects(
    analysis_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve previously generated capstone projects."""
    projects = await get_capstone_projects(analysis_id, user.user_id)
    if not projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No capstone projects found for this analysis",
        )
    return {"analysis_id": analysis_id, "projects": projects}


@router.put(
    "/{project_id}/select",
    summary="Toggle project selection",
)
async def select_project(
    project_id: str,
    selected: bool = True,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Mark or unmark a capstone project as selected."""
    result = await toggle_capstone_selected(project_id, user.user_id, selected)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return {"id": project_id, "is_selected": selected}
