"""
Shortlist — Scaffold Generator Node

Generates a production-ready repository scaffold from
a project description, tech stack, and optional capstone context.
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm, LLMTask
from app.prompts.scaffold_gen import SCAFFOLD_SYSTEM_PROMPT, build_scaffold_user_prompt
from app.logging_config import get_logger

logger = get_logger("agents.scaffold_node")

# Maximum total size of scaffold content to prevent abuse (512 KB)
MAX_SCAFFOLD_CONTENT_BYTES = 512 * 1024

# Allowed file extension whitelist to prevent malicious paths
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml", ".cfg",
    ".md", ".txt", ".sql", ".sh", ".bash", ".dockerfile", ".env",
    ".gitignore", ".dockerignore", ".editorconfig", ".prettierrc",
    ".eslintrc", ".ini", ".lock", ".xml", ".gradle", ".properties",
}

# Path components that are forbidden (security)
FORBIDDEN_PATH_PARTS = {"__pycache__", "node_modules", ".git", "..", "~"}


def _sanitize_path(path: str) -> str | None:
    """Validate and sanitize a file path. Returns None if invalid."""
    path = path.strip().lstrip("/").lstrip("\\")
    if not path or len(path) > 300:
        return None

    # Block path traversal
    parts = re.split(r"[/\\]", path)
    for part in parts:
        if part in FORBIDDEN_PATH_PARTS:
            return None
        if part.startswith(".") and part not in {
            ".env", ".env.example", ".gitignore", ".dockerignore",
            ".editorconfig", ".prettierrc", ".eslintrc", ".github",
        }:
            # Reject non-whitelisted dotfiles
            return None

    # Enforce file extension whitelist (ignore extensionless files like Makefile, Dockerfile)
    filename = parts[-1]
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Blocked file with disallowed extension: {path} (ext={ext})")
            return None

    return "/".join(parts)


def _parse_scaffold_response(content: str) -> dict:
    """Parse the LLM response into a scaffold dict."""
    # Try to extract JSON from markdown code blocks if present
    cleaned = content.strip()
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1).strip()

    result = json.loads(cleaned)

    if not isinstance(result, dict):
        raise ValueError("Scaffold response is not a JSON object")

    if "files" not in result or not isinstance(result["files"], list):
        raise ValueError("Scaffold response missing 'files' array")

    return result


def _validate_scaffold(scaffold: dict) -> dict:
    """Validate and sanitize scaffold output."""
    files = []
    total_size = 0

    for raw_file in scaffold.get("files", []):
        if not isinstance(raw_file, dict):
            continue

        path = _sanitize_path(raw_file.get("path", ""))
        if not path:
            logger.warning(f"Skipping file with invalid path: {raw_file.get('path')}")
            continue

        content = str(raw_file.get("content", ""))
        total_size += len(content.encode("utf-8", errors="replace"))

        if total_size > MAX_SCAFFOLD_CONTENT_BYTES:
            logger.warning("Scaffold content exceeds size limit, truncating files list")
            break

        files.append({
            "path": path,
            "content": content,
            "language": str(raw_file.get("language", "text"))[:30],
            "description": str(raw_file.get("description", ""))[:300],
        })

    # Ensure project_name is safe
    project_name = re.sub(
        r"[^a-z0-9\-]", "",
        str(scaffold.get("project_name", "scaffold-project")).lower(),
    )[:80] or "scaffold-project"

    file_tree = str(scaffold.get("file_tree", ""))[:5000]

    return {
        "project_name": project_name,
        "files": files,
        "file_tree": file_tree,
    }


async def scaffold_generator_node(state: AgentState) -> dict:
    """
    Scaffold Generator Agent Node.

    Input (from state):
        - scaffold_project_title: Title of the project to scaffold
        - scaffold_project_description: Description of the project
        - scaffold_tech_stack: List of technologies
        - scaffold_options: Dict with include_docker, include_ci, include_tests
        - generated_projects: (optional) List of capstone project ideas for context

    Output (to state):
        - scaffold_files: List of generated file dicts
        - scaffold_file_tree: ASCII file tree
        - scaffold_project_name: Kebab-case project name
    """
    logger.info("Scaffold Generator node started")

    try:
        llm = get_llm(task=LLMTask.ANALYSIS, temperature=0.4)

        title = state.get("scaffold_project_title", "Untitled Project")
        description = state.get("scaffold_project_description", "")
        tech_stack = state.get("scaffold_tech_stack", [])
        options = state.get("scaffold_options", {})

        # Try to pull context from generated capstone projects
        architecture = None
        key_features = None
        complexity_level = None
        recruiter_context = None

        projects = state.get("generated_projects") or []
        if projects and isinstance(projects, list) and len(projects) > 0:
            # Use the first project's context
            project = projects[0]
            if isinstance(project, dict):
                arch = project.get("architecture")
                if isinstance(arch, dict):
                    architecture = arch.get("description")
                elif isinstance(arch, str):
                    architecture = arch
                key_features = project.get("key_features")
                complexity_level = project.get("complexity_level")
                recruiter_context = project.get("recruiter_match_reasoning")

        user_prompt = build_scaffold_user_prompt(
            project_title=title,
            project_description=description,
            tech_stack=tech_stack,
            include_docker=options.get("include_docker", True),
            include_ci=options.get("include_ci", True),
            include_tests=options.get("include_tests", True),
            architecture=architecture,
            key_features=key_features,
            complexity_level=complexity_level,
            recruiter_context=recruiter_context,
        )

        messages = [
            SystemMessage(content=SCAFFOLD_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = await llm.ainvoke(messages)

        raw_scaffold = _parse_scaffold_response(response.content)
        validated = _validate_scaffold(raw_scaffold)

        logger.info(
            f"Scaffold Generator produced {len(validated['files'])} files "
            f"for project '{validated['project_name']}'"
        )

        return {
            "scaffold_files": validated["files"],
            "scaffold_file_tree": validated["file_tree"],
            "scaffold_project_name": validated["project_name"],
            "current_phase": "scaffold_generation_complete",
            "messages": [response],
        }

    except json.JSONDecodeError as e:
        logger.error(f"Scaffold Generator: LLM returned invalid JSON: {e}")
        return {
            "errors": [f"Scaffold generation failed: invalid LLM response"],
            "current_phase": "scaffold_generation_failed",
            "messages": [],
        }
    except Exception as e:
        logger.error(f"Scaffold Generator node failed: {e}", exc_info=True)
        return {
            "errors": [f"Scaffold generation failed: {str(e)}"],
            "current_phase": "scaffold_generation_failed",
            "messages": [],
        }
