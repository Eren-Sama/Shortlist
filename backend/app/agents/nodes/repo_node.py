"""
Shortlist — Repo Analysis Node

Analyzes a GitHub repository and generates a recruiter scorecard.
Uses GitHub API for data collection, LLM for scoring.
"""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.services.github_analyzer import analyze_github_repo, RepoAnalysisResult
from app.llm.provider import get_llm, LLMTask
from app.prompts.repo_analysis import REPO_SCORING_SYSTEM_PROMPT, build_repo_user_prompt
from app.logging_config import get_logger

logger = get_logger("agents.repo_node")


def _result_to_prompt_args(result: RepoAnalysisResult) -> dict[str, Any]:
    """Convert RepoAnalysisResult to prompt builder args."""
    return {
        "repo_name": result.metadata.full_name,
        "description": result.metadata.description or "",
        "primary_language": result.metadata.primary_language or "Unknown",
        "languages": result.metadata.languages,
        "stars": result.metadata.stars,
        "topics": result.metadata.topics,
        "has_readme": result.metadata.has_readme,
        "has_license": result.metadata.has_license,
        "has_tests": result.file_analysis.has_tests,
        "has_ci": result.file_analysis.has_ci,
        "has_docker": result.file_analysis.has_docker,
        "total_files": result.file_analysis.total_files,
        "code_files": result.file_analysis.code_files,
        "test_files": result.file_analysis.test_files,
        "config_files": result.file_analysis.config_files,
        "quality_files": result.file_analysis.quality_files,
        "estimated_loc": result.file_analysis.estimated_loc,
        "readme_content": result.readme_content,
        "sample_code": result.sample_code_files,
    }


def _parse_scorecard(content: str) -> dict:
    """Parse LLM response into scorecard dict. Handles markdown code blocks."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line (```json) and last line (```)
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        content = content.strip()
    
    # Try to find JSON object if surrounded by other text
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse scorecard JSON, returning defaults")
        return {
            "code_quality": {"score": 5.0, "details": "Unable to parse", "suggestions": []},
            "test_coverage": {"score": 5.0, "details": "Unable to parse", "suggestions": []},
            "complexity": {"score": 5.0, "details": "Unable to parse", "suggestions": []},
            "structure": {"score": 5.0, "details": "Unable to parse", "suggestions": []},
            "deployment_readiness": {"score": 5.0, "details": "Unable to parse", "suggestions": []},
            "overall_score": 5.0,
            "summary": content[:500] if content else "Analysis completed but response parsing failed.",
            "top_improvements": ["Retry analysis for detailed feedback"],
        }


async def repo_analysis_node(state: AgentState) -> dict:
    """
    Repo Analysis Agent Node.
    
    Input (from state):
        - repo_url: GitHub repository URL
        
    Output (to state):
        - repo_scorecard: Complete recruiter scorecard
        - current_phase: Updated phase status
        - errors: Any errors encountered
    """
    repo_url = state.get("repo_url")
    
    if not repo_url:
        logger.error("Repo analysis called without repo_url")
        return {
            "current_phase": "repo_analysis_failed",
            "errors": (state.get("errors") or []) + ["No repository URL provided"],
        }
    
    logger.info(f"Starting repo analysis for: {repo_url}")
    
    try:
        # Step 1: Fetch repo data via GitHub API
        result = await analyze_github_repo(repo_url)
        
        logger.info(
            f"Fetched {result.metadata.full_name}: "
            f"{result.file_analysis.total_files} files, "
            f"{result.file_analysis.code_files} code files"
        )
        
        # Step 2: Generate scorecard using LLM
        llm = get_llm(task=LLMTask.SCORING)
        
        prompt_args = _result_to_prompt_args(result)
        
        # Truncate sample code to prevent token overflow
        if "sample_code" in prompt_args and isinstance(prompt_args["sample_code"], dict):
            truncated = {}
            for fpath, content in prompt_args["sample_code"].items():
                truncated[fpath] = content[:8000] if isinstance(content, str) else content
            prompt_args["sample_code"] = truncated
        
        user_prompt = build_repo_user_prompt(**prompt_args)
        
        messages = [
            SystemMessage(content=REPO_SCORING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        
        # Attempt with retry on JSON parse failure (consistent with other nodes)
        scorecard = None
        for attempt in range(2):
            response = await llm.ainvoke(messages)
            scorecard = _parse_scorecard(response.content)
            # If we got default fallback scores, retry once
            if scorecard.get("summary", "").startswith("Unable to parse") or (
                attempt == 0 and all(
                    scorecard.get(k, {}).get("details") == "Unable to parse"
                    for k in ("code_quality", "test_coverage", "complexity")
                )
            ):
                if attempt == 0:
                    messages.append(HumanMessage(
                        content="Your response was not valid JSON. Return ONLY a JSON object with no markdown fences or extra text."
                    ))
                    logger.warning("Repo scoring: retrying due to invalid JSON")
                    continue
            break
        
        # Add repo metadata to scorecard
        scorecard["repo_url"] = repo_url
        scorecard["repo_name"] = result.metadata.full_name
        scorecard["primary_language"] = result.metadata.primary_language
        scorecard["total_files"] = result.file_analysis.total_files
        scorecard["total_lines"] = result.file_analysis.estimated_loc
        
        logger.info(
            f"Repo analysis complete: {result.metadata.full_name} — "
            f"Overall Score: {scorecard.get('overall_score', 'N/A')}/10"
        )
        
        return {
            "repo_scorecard": scorecard,
            "current_phase": "repo_analysis_complete",
            "messages": [],
        }
        
    except ValueError as e:
        logger.warning(f"Invalid repo URL or not found: {e}")
        return {
            "current_phase": "repo_analysis_failed",
            "errors": (state.get("errors") or []) + [str(e)],
        }
    except RuntimeError as e:
        logger.error(f"Runtime error during repo analysis: {e}")
        return {
            "current_phase": "repo_analysis_failed",
            "errors": (state.get("errors") or []) + [str(e)],
        }
    except Exception as e:
        logger.error(f"Unexpected error in repo analysis: {e}", exc_info=True)
        return {
            "current_phase": "repo_analysis_failed",
            "errors": (state.get("errors") or []) + ["Repository analysis encountered an error"],
        }
