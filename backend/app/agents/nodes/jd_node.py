"""
Shortlist — JD Analysis Node

Extracts structured skill profiles from raw job description text.
Uses LLM with Pydantic structured output for reliable extraction.
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm, LLMTask
from app.prompts.jd_analysis import JD_SYSTEM_PROMPT, build_jd_user_prompt
from app.logging_config import get_logger

logger = get_logger("agents.jd_node")


async def jd_analysis_node(state: AgentState) -> dict:
    """
    JD Analysis Agent Node.

    Input (from state):
        - jd_text: Raw job description
        - role: Target role
        - company_type: Company archetype

    Output (to state):
        - skill_profile: Extracted skills with weights
        - engineering_expectations: What the role demands
        - messages: Updated conversation history
    """
    logger.info(f"JD Analysis node started for role: {state.get('role', 'unknown')}")

    try:
        llm = get_llm(task=LLMTask.ANALYSIS)

        messages = [
            SystemMessage(content=JD_SYSTEM_PROMPT),
            HumanMessage(content=build_jd_user_prompt(
                jd_text=state["jd_text"],
                role=state["role"],
                company_type=state["company_type"],
                geography=state.get("geography"),
            )),
        ]

        # Attempt up to 2 tries for valid JSON
        parsed = None
        for attempt in range(2):
            response = await llm.ainvoke(messages)
            raw = response.content.strip()

            # Robustly strip markdown fences (```json, ```, etc.)
            raw = re.sub(r'^```[a-zA-Z]*\s*', '', raw)
            raw = re.sub(r'```\s*$', '', raw)
            raw = raw.strip()

            # If still not starting with {, try to find the JSON object
            if not raw.startswith("{"):
                brace = raw.find("{")
                if brace >= 0:
                    raw = raw[brace:]
                    end = raw.rfind("}")
                    if end > 0:
                        raw = raw[:end + 1]

            try:
                parsed = json.loads(raw)
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: LLM returned invalid JSON: {e}")
                # On retry, add feedback to messages
                if attempt == 0:
                    messages.append(HumanMessage(
                        content="Your response was not valid JSON. Please return ONLY the JSON object as specified, with no markdown, no explanation, no extra text."
                    ))

        if parsed is None:
            logger.warning("LLM did not return valid JSON after retries, wrapping raw response")
            parsed = {
                "skills": [],
                "experience_level": "mid",
                "domain": state.get("role", "Software Engineering"),
                "engineering_expectations": [],
                "key_responsibilities": [],
                "summary": response.content[:8000],
            }

        logger.info(
            f"JD Analysis complete: {len(parsed.get('skills', []))} skills extracted"
        )

        return {
            "skill_profile": parsed,
            "engineering_expectations": parsed.get("engineering_expectations", []),
            "current_phase": "jd_analysis_complete",
            "messages": [response],
        }

    except Exception as e:
        logger.error(f"JD Analysis node failed: {e}", exc_info=True)
        return {
            "errors": [f"JD analysis failed: {str(e)}"],
            "current_phase": "jd_analysis_failed",
            "messages": [],
        }
