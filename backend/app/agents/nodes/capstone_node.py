"""
Shortlist — Capstone Generator Node

Generates tailored capstone project ideas based on
the analyzed skill profile and company modifiers.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm, LLMTask
from app.prompts.capstone_gen import CAPSTONE_SYSTEM_PROMPT, build_capstone_user_prompt
from app.logging_config import get_logger

logger = get_logger("agents.capstone_node")


async def capstone_generator_node(state: AgentState) -> dict:
    """
    Capstone Generator Agent Node.

    Input (from state):
        - skill_profile: Weighted skill profile
        - company_modifiers: Company-type adjustments
        - role: Target role
        - company_type: Company archetype

    Output (to state):
        - generated_projects: List of 3 tailored project ideas
        - messages: Updated conversation history
    """
    logger.info("Capstone Generator node started")

    try:
        llm = get_llm(task=LLMTask.ANALYSIS, temperature=0.7)

        skill_profile = state.get("skill_profile", {})
        company_modifiers = state.get("company_modifiers", {})

        messages = [
            SystemMessage(content=CAPSTONE_SYSTEM_PROMPT),
            HumanMessage(content=build_capstone_user_prompt(
                skill_profile=skill_profile,
                company_modifiers=company_modifiers,
                role=state.get("role", "Software Engineer"),
                company_type=state.get("company_type", "mid_level"),
            )),
        ]

        response = await llm.ainvoke(messages)

        parsed = None
        # Attempt to parse, with one retry if JSON is malformed
        for attempt in range(2):
            raw = response.content.strip()
            # Strip markdown fences
            if raw.startswith("```"):
                first_nl = raw.index("\n") if "\n" in raw else 3
                raw = raw[first_nl:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            try:
                parsed = json.loads(raw)
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Capstone attempt {attempt + 1}: invalid JSON: {e}")
                if attempt == 0:
                    messages.append(HumanMessage(content="Your response was not valid JSON. Return ONLY the JSON object with no markdown."))
                    response = await llm.ainvoke(messages)

        if parsed is None:
            logger.warning("Capstone: LLM did not return valid JSON after retries")
            projects = []
        else:
            if isinstance(parsed, dict) and "projects" in parsed:
                projects = parsed["projects"]
            elif isinstance(parsed, list):
                projects = parsed
            else:
                projects = []

        logger.info(f"Capstone Generator produced {len(projects)} project ideas")

        return {
            "generated_projects": projects,
            "current_phase": "capstone_generation_complete",
            "messages": [response],
        }

    except Exception as e:
        logger.error(f"Capstone Generator node failed: {e}", exc_info=True)
        return {
            "errors": [f"Capstone generation failed: {str(e)}"],
            "current_phase": "capstone_generation_failed",
            "messages": [],
        }
