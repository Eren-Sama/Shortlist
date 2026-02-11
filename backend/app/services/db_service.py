"""
Shortlist — Database Service Layer

Handles all Supabase CRUD operations for
JD analyses, capstone projects, repo analyses, scaffolds, and portfolio outputs.
Uses the service-role key (bypasses RLS) for backend operations.
"""

from typing import Optional
from uuid import UUID

from supabase import AsyncClient

from app.database import get_supabase
from app.logging_config import get_logger

logger = get_logger("services.db")

# JD Analyses

async def create_jd_analysis(
    user_id: str,
    jd_text: str,
    role: str,
    company_type: str,
    geography: Optional[str] = None,
) -> dict:
    """Insert a new pending JD analysis record."""
    db = get_supabase()
    result = await db.table("jd_analyses").insert({
        "user_id": user_id,
        "jd_text": jd_text,
        "role": role,
        "company_type": company_type,
        "geography": geography,
        "status": "pending",
    }).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError("Failed to insert JD analysis record")

    logger.info(f"Created JD analysis {record['id']} for user {user_id}")
    return record

async def update_jd_analysis(
    analysis_id: str,
    user_id: str,
    *,
    skill_profile: Optional[dict] = None,
    engineering_expectations: Optional[dict] = None,
    company_modifiers: Optional[dict] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> dict:
    """Update a JD analysis record with results. Always filters by user_id for IDOR protection."""
    db = get_supabase()
    payload: dict = {}
    if skill_profile is not None:
        payload["skill_profile"] = skill_profile
    if engineering_expectations is not None:
        payload["engineering_expectations"] = engineering_expectations
    if company_modifiers is not None:
        payload["company_modifiers"] = company_modifiers
    if status is not None:
        payload["status"] = status
    if error_message is not None:
        payload["error_message"] = error_message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    if not payload:
        raise ValueError("No fields to update")

    result = await db.table("jd_analyses").update(payload).eq(
        "id", analysis_id
    ).eq("user_id", user_id).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError(f"Failed to update JD analysis {analysis_id}")

    logger.info(f"Updated JD analysis {analysis_id}: status={status}")
    return record

async def get_jd_analysis(analysis_id: str, user_id: str) -> Optional[dict]:
    """Fetch a single JD analysis, ensuring user ownership."""
    db = get_supabase()
    result = await db.table("jd_analyses").select("*").eq(
        "id", analysis_id
    ).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

async def list_jd_analyses(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List JD analyses for a user with pagination. Returns (records, total_count)."""
    db = get_supabase()

    # Get paginated results
    result = await db.table("jd_analyses").select(
        "id, role, company_type, geography, status, processing_time_ms, created_at, updated_at",
        count="exact",
    ).eq("user_id", user_id).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()

    total = result.count if result.count is not None else len(result.data)
    return result.data or [], total

async def delete_jd_analysis(analysis_id: str, user_id: str) -> bool:
    """Delete a JD analysis and all cascaded records (capstones, fitness, etc.)."""
    db = get_supabase()
    result = await db.table("jd_analyses").delete().eq(
        "id", analysis_id
    ).eq("user_id", user_id).execute()

    deleted = bool(result.data)
    if deleted:
        logger.info(f"Deleted JD analysis {analysis_id} for user {user_id}")
    return deleted

# Capstone Projects

async def create_capstone_projects(
    user_id: str,
    analysis_id: str,
    projects: list[dict],
) -> list[dict]:
    """Insert generated capstone project records."""
    db = get_supabase()

    rows = []
    for project in projects:
        arch = project.get("architecture", {})
        arch_text = (
            arch.get("description", "")
            if isinstance(arch, dict)
            else str(arch or "")
        )

        rows.append({
            "user_id": user_id,
            "analysis_id": analysis_id,
            "title": project.get("title", "Untitled Project"),
            "problem_statement": project.get("problem_statement", ""),
            "architecture": arch_text,
            "tech_stack": project.get("tech_stack", []),
            "complexity": project.get("complexity_level", 3),
            "estimated_days": project.get("estimated_days", 14),
            "resume_bullet": project.get("resume_bullet"),
            "differentiator": project.get("differentiator"),
            "key_features": project.get("key_features", []),
            "recruiter_match_reasoning": project.get("recruiter_match_reasoning"),
        })

    if not rows:
        return []

    result = await db.table("capstone_projects").insert(rows).execute()

    logger.info(
        f"Created {len(result.data)} capstone projects for analysis {analysis_id}"
    )
    return result.data or []

async def get_capstone_projects(
    analysis_id: str,
    user_id: str,
) -> list[dict]:
    """Fetch all capstone projects for an analysis."""
    db = get_supabase()
    result = await db.table("capstone_projects").select("*").eq(
        "analysis_id", analysis_id
    ).eq("user_id", user_id).order("created_at").execute()

    return result.data or []

async def toggle_capstone_selected(
    project_id: str,
    user_id: str,
    selected: bool,
) -> Optional[dict]:
    """Mark a capstone project as selected/deselected."""
    db = get_supabase()
    result = await db.table("capstone_projects").update(
        {"is_selected": selected}
    ).eq("id", project_id).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

# Repo Analyses

async def create_repo_analysis(
    user_id: str,
    github_url: str,
) -> dict:
    """Insert a new pending repo analysis record."""
    db = get_supabase()
    result = await db.table("repo_analyses").insert({
        "user_id": user_id,
        "github_url": github_url,
        "status": "pending",
    }).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError("Failed to insert repo analysis record")

    logger.info(f"Created repo analysis {record['id']} for user {user_id}")
    return record

async def update_repo_analysis(
    analysis_id: str,
    user_id: str,
    *,
    scorecard: Optional[dict] = None,
    repo_name: Optional[str] = None,
    primary_language: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> dict:
    """Update a repo analysis record with results. Always filters by user_id for IDOR protection."""
    db = get_supabase()
    payload: dict = {}
    if scorecard is not None:
        payload["scorecard"] = scorecard
    if repo_name is not None:
        payload["repo_name"] = repo_name
    if primary_language is not None:
        payload["primary_language"] = primary_language
    if status is not None:
        payload["status"] = status
    if error_message is not None:
        payload["error_message"] = error_message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    if not payload:
        raise ValueError("No fields to update")

    result = await db.table("repo_analyses").update(payload).eq(
        "id", analysis_id
    ).eq("user_id", user_id).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError(f"Failed to update repo analysis {analysis_id}")

    logger.info(f"Updated repo analysis {analysis_id}: status={status}")
    return record

async def get_repo_analysis(analysis_id: str, user_id: str) -> Optional[dict]:
    """Fetch a single repo analysis, ensuring user ownership."""
    db = get_supabase()
    result = await db.table("repo_analyses").select("*").eq(
        "id", analysis_id
    ).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

async def list_repo_analyses(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List repo analyses for a user with pagination."""
    db = get_supabase()

    result = await db.table("repo_analyses").select(
        "id, github_url, repo_name, primary_language, status, scorecard, processing_time_ms, created_at, updated_at",
        count="exact",
    ).eq("user_id", user_id).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()

    total = result.count if result.count is not None else len(result.data)
    return result.data or [], total

# Scaffolds

async def create_scaffold(
    user_id: str,
    project_title: str,
    project_description: str,
    tech_stack: list[str],
    *,
    project_id: Optional[str] = None,
    include_docker: bool = True,
    include_ci: bool = True,
    include_tests: bool = True,
) -> dict:
    """Insert a new pending scaffold record."""
    db = get_supabase()
    payload = {
        "user_id": user_id,
        "project_title": project_title,
        "project_description": project_description,
        "tech_stack": tech_stack,
        "include_docker": include_docker,
        "include_ci": include_ci,
        "include_tests": include_tests,
        "status": "pending",
    }
    if project_id:
        payload["project_id"] = project_id

    result = await db.table("scaffolds").insert(payload).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError("Failed to insert scaffold record")

    logger.info(f"Created scaffold {record['id']} for user {user_id}")
    return record

async def update_scaffold(
    scaffold_id: str,
    user_id: str,
    *,
    files: Optional[list[dict]] = None,
    file_tree: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> dict:
    """Update a scaffold record with results. Always filters by user_id for IDOR protection."""
    db = get_supabase()
    payload: dict = {}
    if files is not None:
        payload["files"] = files
    if file_tree is not None:
        payload["file_tree"] = file_tree
    if status is not None:
        payload["status"] = status
    if error_message is not None:
        payload["error_message"] = error_message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    if not payload:
        raise ValueError("No fields to update")

    result = await db.table("scaffolds").update(payload).eq(
        "id", scaffold_id
    ).eq("user_id", user_id).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError(f"Failed to update scaffold {scaffold_id}")

    logger.info(f"Updated scaffold {scaffold_id}: status={status}")
    return record

async def get_scaffold(scaffold_id: str, user_id: str) -> Optional[dict]:
    """Fetch a single scaffold, ensuring user ownership."""
    db = get_supabase()
    result = await db.table("scaffolds").select("*").eq(
        "id", scaffold_id
    ).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

async def list_scaffolds(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List scaffolds for a user with pagination."""
    db = get_supabase()

    result = await db.table("scaffolds").select(
        "id, project_id, project_title, tech_stack, status, processing_time_ms, created_at, updated_at",
        count="exact",
    ).eq("user_id", user_id).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()

    total = result.count if result.count is not None else len(result.data)
    return result.data or [], total

# Portfolio Outputs

async def create_portfolio_output(
    user_id: str,
    project_title: str,
    project_description: str,
    tech_stack: list[str],
    *,
    target_role: Optional[str] = None,
    analysis_id: Optional[str] = None,
) -> dict:
    """Insert a new pending portfolio output record."""
    db = get_supabase()
    payload = {
        "user_id": user_id,
        "project_title": project_title,
        "project_description": project_description,
        "tech_stack": tech_stack,
        "status": "pending",
    }
    if target_role:
        payload["target_role"] = target_role
    if analysis_id:
        payload["analysis_id"] = analysis_id

    result = await db.table("portfolio_outputs").insert(payload).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError("Failed to insert portfolio output record")

    logger.info(f"Created portfolio output {record['id']} for user {user_id}")
    return record

async def update_portfolio_output(
    portfolio_id: str,
    user_id: str,
    *,
    readme_markdown: Optional[str] = None,
    resume_bullets: Optional[list[dict]] = None,
    demo_script: Optional[dict] = None,
    linkedin_post: Optional[dict] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> dict:
    """Update a portfolio output record with results. Always filters by user_id for IDOR protection."""
    db = get_supabase()
    payload: dict = {}
    if readme_markdown is not None:
        payload["readme_markdown"] = readme_markdown
    if resume_bullets is not None:
        payload["resume_bullets"] = resume_bullets
    if demo_script is not None:
        payload["demo_script"] = demo_script
    if linkedin_post is not None:
        payload["linkedin_post"] = linkedin_post
    if status is not None:
        payload["status"] = status
    if error_message is not None:
        payload["error_message"] = error_message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    if not payload:
        raise ValueError("No fields to update")

    result = await db.table("portfolio_outputs").update(payload).eq(
        "id", portfolio_id
    ).eq("user_id", user_id).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError(f"Failed to update portfolio output {portfolio_id}")

    logger.info(f"Updated portfolio output {portfolio_id}: status={status}")
    return record

async def get_portfolio_output(portfolio_id: str, user_id: str) -> Optional[dict]:
    """Fetch a single portfolio output, ensuring user ownership."""
    db = get_supabase()
    result = await db.table("portfolio_outputs").select("*").eq(
        "id", portfolio_id
    ).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

async def list_portfolio_outputs(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List portfolio outputs for a user with pagination."""
    db = get_supabase()

    result = await db.table("portfolio_outputs").select(
        "id, project_title, tech_stack, target_role, status, processing_time_ms, created_at, updated_at",
        count="exact",
    ).eq("user_id", user_id).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()

    total = result.count if result.count is not None else len(result.data)
    return result.data or [], total

# Resume Fitness Scores

async def create_fitness_score(
    user_id: str,
    analysis_id: str,
    resume_text: str,
) -> dict:
    """Insert a new pending fitness score record."""
    db = get_supabase()
    result = await db.table("resume_fitness_scores").insert({
        "user_id": user_id,
        "analysis_id": analysis_id,
        "resume_text": resume_text,
        "status": "pending",
    }).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError("Failed to insert fitness score record")

    logger.info(f"Created fitness score {record['id']} for user {user_id}")
    return record

async def update_fitness_score(
    fitness_id: str,
    user_id: str,
    *,
    fitness_score: Optional[float] = None,
    verdict: Optional[str] = None,
    matched_skills: Optional[list] = None,
    missing_skills: Optional[list] = None,
    strengths: Optional[list] = None,
    improvements: Optional[list] = None,
    detailed_feedback: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> dict:
    """Update a fitness score record with results."""
    db = get_supabase()
    payload: dict = {}
    if fitness_score is not None:
        payload["fitness_score"] = fitness_score
    if verdict is not None:
        payload["verdict"] = verdict
    if matched_skills is not None:
        payload["matched_skills"] = matched_skills
    if missing_skills is not None:
        payload["missing_skills"] = missing_skills
    if strengths is not None:
        payload["strengths"] = strengths
    if improvements is not None:
        payload["improvements"] = improvements
    if detailed_feedback is not None:
        payload["detailed_feedback"] = detailed_feedback
    if status is not None:
        payload["status"] = status
    if error_message is not None:
        payload["error_message"] = error_message
    if processing_time_ms is not None:
        payload["processing_time_ms"] = processing_time_ms

    if not payload:
        raise ValueError("No fields to update")

    result = await db.table("resume_fitness_scores").update(payload).eq(
        "id", fitness_id
    ).eq("user_id", user_id).execute()

    record = result.data[0] if result.data else None
    if not record:
        raise RuntimeError(f"Failed to update fitness score {fitness_id}")

    logger.info(f"Updated fitness score {fitness_id}: status={status}")
    return record

async def get_fitness_score(fitness_id: str, user_id: str) -> Optional[dict]:
    """Fetch a single fitness score, ensuring user ownership."""
    db = get_supabase()
    result = await db.table("resume_fitness_scores").select("*").eq(
        "id", fitness_id
    ).eq("user_id", user_id).execute()

    return result.data[0] if result.data else None

async def list_fitness_scores(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List fitness scores for a user with pagination."""
    db = get_supabase()

    result = await db.table("resume_fitness_scores").select(
        "id, analysis_id, fitness_score, verdict, status, processing_time_ms, created_at",
        count="exact",
    ).eq("user_id", user_id).order(
        "created_at", desc=True
    ).range(offset, offset + limit - 1).execute()

    total = result.count if result.count is not None else len(result.data)
    return result.data or [], total
