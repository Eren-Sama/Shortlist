"""
Shortlist — Portfolio Optimizer Node

LangGraph node that generates polished portfolio materials:
README, resume bullets, demo script, and LinkedIn post.
"""

import json
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm, LLMTask
from app.prompts.portfolio_opt import (
    PORTFOLIO_SYSTEM_PROMPT,
    build_portfolio_user_prompt,
)
from app.logging_config import get_logger

logger = get_logger("agents.portfolio_node")

# ── Size Limits ──
MAX_README_LENGTH = 20_000       # 20 KB
MAX_BULLET_LENGTH = 300
MAX_POST_BODY_LENGTH = 3_000
MAX_DEMO_STEPS = 15


def _parse_portfolio_response(raw: str) -> dict:
    """Parse the LLM response into a portfolio dict.

    Handles markdown-wrapped JSON (```json ... ```) and plain JSON.
    """
    text = raw.strip()

    # Strip markdown fences
    if text.startswith("```"):
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse portfolio JSON: {e}")
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in portfolio response: {e}")
        else:
            raise ValueError(f"No JSON object found in portfolio response: {e}")

    return data


def _validate_portfolio(data: dict) -> dict:
    """Validate and sanitize the parsed portfolio output."""
    errors: list[str] = []

    # ── README ──
    readme = data.get("readme_markdown", "")
    if not readme or not isinstance(readme, str):
        errors.append("Missing or invalid readme_markdown")
    elif len(readme) > MAX_README_LENGTH:
        data["readme_markdown"] = readme[:MAX_README_LENGTH]
        logger.warning("README truncated to size limit")

    # ── Resume Bullets ──
    bullets = data.get("resume_bullets", [])
    if not isinstance(bullets, list) or len(bullets) == 0:
        errors.append("Missing or empty resume_bullets")
    else:
        valid_bullets = []
        for b in bullets:
            if isinstance(b, dict) and b.get("bullet"):
                bullet_text = str(b["bullet"])[:MAX_BULLET_LENGTH]
                valid_bullets.append({
                    "bullet": bullet_text,
                    "keywords": b.get("keywords", []),
                    "impact_type": b.get("impact_type", "technical"),
                })
        data["resume_bullets"] = valid_bullets
        if not valid_bullets:
            errors.append("No valid resume_bullets found")

    # ── Demo Script ──
    demo = data.get("demo_script", {})
    if not isinstance(demo, dict):
        errors.append("Missing or invalid demo_script")
    else:
        if not demo.get("opening_hook"):
            errors.append("demo_script.opening_hook missing")
        if not demo.get("closing_cta"):
            errors.append("demo_script.closing_cta missing")
        steps = demo.get("steps", [])
        if isinstance(steps, list) and len(steps) > MAX_DEMO_STEPS:
            demo["steps"] = steps[:MAX_DEMO_STEPS]
        data["demo_script"] = demo

    # ── LinkedIn Post ──
    post = data.get("linkedin_post", {})
    if not isinstance(post, dict):
        errors.append("Missing or invalid linkedin_post")
    else:
        if not post.get("hook"):
            errors.append("linkedin_post.hook missing")
        body = post.get("body", "")
        if len(str(body)) > MAX_POST_BODY_LENGTH:
            post["body"] = str(body)[:MAX_POST_BODY_LENGTH]
        data["linkedin_post"] = post

    if errors:
        logger.warning(f"Portfolio validation issues: {errors}")
        # Non-critical: we still return what we have, but log issues

    return data


async def portfolio_optimizer_node(state: AgentState) -> dict:
    """Generate polished portfolio materials using an LLM.

    Reads from state:
        - portfolio_project_title, portfolio_project_description
        - portfolio_tech_stack, portfolio_key_features
        - portfolio_repo_score, portfolio_target_role

    Writes to state:
        - portfolio_output: dict with readme, bullets, demo, linkedin
        - current_phase: "portfolio_complete" | "portfolio_error"
    """
    start_time = time.time()
    logger.info("Portfolio Optimizer node started")

    title = state.get("portfolio_project_title", "")
    description = state.get("portfolio_project_description", "")
    tech_stack = state.get("portfolio_tech_stack", [])
    key_features = state.get("portfolio_key_features", [])
    repo_score = state.get("portfolio_repo_score")
    target_role = state.get("portfolio_target_role")

    if not title or not description:
        err = "portfolio_project_title and portfolio_project_description are required"
        logger.error(err)
        return {
            "current_phase": "portfolio_error",
            "errors": [err],
            "messages": [AIMessage(content=f"Portfolio error: {err}")],
        }

    # Build prompts
    user_prompt = build_portfolio_user_prompt(
        project_title=title,
        project_description=description,
        tech_stack=tech_stack,
        key_features=key_features if key_features else None,
        repo_score=repo_score,
        target_role=target_role,
    )

    # Call LLM
    try:
        llm = get_llm(task=LLMTask.ANALYSIS, temperature=0.5)
        messages = [
            SystemMessage(content=PORTFOLIO_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)
        raw = response.content
    except Exception as e:
        err = f"LLM call failed: {e}"
        logger.error(err)
        return {
            "current_phase": "portfolio_error",
            "errors": [err],
            "messages": [AIMessage(content=f"Portfolio error: {err}")],
        }

    # Parse and validate
    try:
        parsed = _parse_portfolio_response(raw)
        validated = _validate_portfolio(parsed)
    except (ValueError, KeyError) as e:
        err = f"Failed to parse portfolio response: {e}"
        logger.error(err)
        return {
            "current_phase": "portfolio_error",
            "errors": [err],
            "messages": [AIMessage(content=f"Portfolio error: {err}")],
        }

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Portfolio optimization complete in {elapsed_ms}ms")

    return {
        "portfolio_output": validated,
        "current_phase": "portfolio_complete",
        "messages": [
            AIMessage(content=f"Portfolio materials generated in {elapsed_ms}ms"),
        ],
    }
