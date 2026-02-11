"""
Shortlist — Scaffold Generator Endpoints

POST /api/v1/scaffold/generate     — Generate a project scaffold
GET  /api/v1/scaffold/{id}         — Get a scaffold by ID
GET  /api/v1/scaffold/             — List scaffolds for the user
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AuthenticatedUser, get_current_user
from app.schemas.scaffold import (
    ScaffoldRequest,
    ScaffoldResponse,
    GeneratedFile,
)
from app.agents.orchestrator import compile_scaffold_pipeline
from app.services.db_service import (
    create_scaffold,
    update_scaffold,
    get_scaffold,
    list_scaffolds,
    get_capstone_projects,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("api.scaffold")


def _safe_parse_file(raw: dict) -> GeneratedFile:
    """Safely parse a raw dict into a validated GeneratedFile."""
    return GeneratedFile(
        path=str(raw.get("path", "unknown"))[:500],
        content=str(raw.get("content", "")),
        language=str(raw.get("language", "text"))[:30],
        description=str(raw.get("description", ""))[:300],
    )


@router.post(
    "/generate",
    response_model=ScaffoldResponse,
    summary="Generate a Project Scaffold",
    description="Creates a production-ready repository structure with boilerplate code.",
)
async def generate_scaffold_endpoint(
    request: ScaffoldRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    1. Create a pending scaffold record
    2. Optionally load capstone project context
    3. Run scaffold pipeline
    4. Persist results and return
    """
    logger.info(
        f"Scaffold generation requested by user {user.user_id} "
        f"for project: {request.project_title}"
    )
    start_time = time.time()

    # If linked to a JD analysis, try to load capstone projects for context
    capstone_context = []
    if request.analysis_id:
        try:
            capstone_context = await get_capstone_projects(
                request.analysis_id, user.user_id
            )
        except Exception as e:
            logger.warning(f"Could not load capstone context: {e}")

    # Step 1: Create pending record
    try:
        record = await create_scaffold(
            user_id=user.user_id,
            project_title=request.project_title,
            project_description=request.project_description,
            tech_stack=request.tech_stack,
            project_id=request.project_id,
            include_docker=request.include_docker,
            include_ci=request.include_ci,
            include_tests=request.include_tests,
        )
        scaffold_id = record["id"]
    except Exception as e:
        logger.error(f"Failed to create scaffold record: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate scaffold generation.",
        )

    # Step 2: Run scaffold pipeline
    try:
        await update_scaffold(scaffold_id, user.user_id, status="processing")

        pipeline = compile_scaffold_pipeline()
        initial_state = {
            "scaffold_project_title": request.project_title,
            "scaffold_project_description": request.project_description,
            "scaffold_tech_stack": request.tech_stack,
            "scaffold_options": {
                "include_docker": request.include_docker,
                "include_ci": request.include_ci,
                "include_tests": request.include_tests,
            },
            "generated_projects": capstone_context if capstone_context else [],
            "messages": [],
            "errors": [],
            # Required state fields with defaults
            "jd_text": "",
            "role": "",
            "company_type": "",
            "user_id": user.user_id,
        }

        final_state = await pipeline.ainvoke(initial_state)

        errors = final_state.get("errors", [])
        if errors:
            elapsed_ms = int((time.time() - start_time) * 1000)
            await update_scaffold(
                scaffold_id,
                user.user_id,
                status="failed",
                error_message=errors[0][:1000],
                processing_time_ms=elapsed_ms,
            )
            logger.warning(f"Scaffold {scaffold_id} failed: {errors[0][:200]}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Scaffold generation could not be completed. Please adjust your input and try again.",
            )

        raw_files = final_state.get("scaffold_files", [])
        file_tree = final_state.get("scaffold_file_tree", "")
        project_name = final_state.get("scaffold_project_name", "scaffold-project")

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Scaffold pipeline failed: {e}", exc_info=True)
        await update_scaffold(
            scaffold_id,
            user.user_id,
            status="failed",
            error_message=str(e)[:1000],
            processing_time_ms=elapsed_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scaffold generation encountered an error. Please try again.",
        )

    # Step 3: Persist results
    elapsed_ms = int((time.time() - start_time) * 1000)
    try:
        await update_scaffold(
            scaffold_id,
            user.user_id,
            files=raw_files,
            file_tree=file_tree,
            status="completed",
            processing_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error(f"Failed to persist scaffold: {e}", exc_info=True)

    # Step 4: Parse and return
    parsed_files = []
    for f in raw_files:
        try:
            parsed_files.append(_safe_parse_file(f))
        except Exception as e:
            logger.warning(f"Failed to parse scaffold file: {e}")
            continue

    logger.info(
        f"Scaffold generation completed in {elapsed_ms}ms — "
        f"{len(parsed_files)} files generated"
    )

    return ScaffoldResponse(
        project_name=project_name,
        files=parsed_files,
        file_tree=file_tree,
        generation_metadata={
            "scaffold_id": scaffold_id,
            "processing_time_ms": elapsed_ms,
            "files_generated": len(parsed_files),
        },
    )


@router.get(
    "/",
    summary="List scaffolds",
)
async def list_scaffolds_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List scaffolds for the authenticated user."""
    scaffolds, total = await list_scaffolds(user.user_id, limit=limit, offset=offset)
    return {
        "scaffolds": scaffolds,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{scaffold_id}",
    summary="Get scaffold by ID",
)
async def get_scaffold_endpoint(
    scaffold_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieve a scaffold by ID, ensuring user ownership."""
    record = await get_scaffold(scaffold_id, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scaffold not found",
        )

    # Parse files safely
    raw_files = record.get("files", [])
    parsed_files = []
    if isinstance(raw_files, list):
        for f in raw_files:
            try:
                parsed_files.append(_safe_parse_file(f))
            except Exception:
                continue

    return ScaffoldResponse(
        project_name=record.get("project_title", "scaffold-project"),
        files=parsed_files,
        file_tree=record.get("file_tree", ""),
        generation_metadata={
            "scaffold_id": record["id"],
            "processing_time_ms": record.get("processing_time_ms"),
            "status": record.get("status"),
        },
    )
