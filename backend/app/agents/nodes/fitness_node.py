"""
Shortlist — Resume Fitness Scorer Node

LLM-powered evaluation of resume fit against a JD analysis.
"""

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm, LLMTask
from app.logging_config import get_logger

logger = get_logger("agents.fitness")

FITNESS_SYSTEM_PROMPT = """You are an expert technical recruiter and talent assessor with 15+ years of experience evaluating engineering candidates.

Your task: Evaluate how well a candidate's resume matches a specific job description.

You MUST return ONLY valid JSON with NO markdown fences, NO commentary, NO extra text.

Return this exact JSON structure:
{
  "fitness_score": <number 0-100>,
  "verdict": "<strong_fit|good_fit|partial_fit|weak_fit>",
  "matched_skills": [{"name": "<skill>", "evidence": "<brief evidence from resume>"}],
  "missing_skills": [{"name": "<skill>", "importance": "<critical|important|nice_to_have>", "suggestion": "<how to acquire>"}],
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "improvements": [{"area": "<area>", "current_state": "<what the resume currently shows for this area>", "recommended_action": "<specific actionable step to improve>", "impact": "<high|medium|low>"}],
  "detailed_feedback": "<2-3 paragraph comprehensive assessment>"
}

Scoring guidelines:
- 85-100: Strong fit — candidate exceeds most requirements
- 70-84: Good fit — candidate meets core requirements with minor gaps
- 50-69: Partial fit — significant gaps but transferable skills present
- 0-49: Weak fit — major skill/experience mismatches

Be specific with evidence. Reference actual resume content. Be constructive with improvements."""


def _build_fitness_prompt(
    role: str,
    company_type: str,
    skills: list[dict],
    experience_level: str,
    expectations: list[dict],
    responsibilities: list[str],
    resume_text: str,
) -> str:
    """Build the evaluation prompt with JD context + resume."""
    skills_text = "\n".join(
        f"  - {s.get('name', '?')} (weight: {s.get('weight', 5)}/10, source: {s.get('source', 'inferred')})"
        for s in skills[:25]
    )
    expectations_text = "\n".join(
        f"  - {e.get('dimension', '?')}: {e.get('description', '')} (importance: {e.get('importance', 5)}/10)"
        for e in expectations[:10]
    )
    responsibilities_text = "\n".join(
        f"  - {r}" for r in responsibilities[:10]
    )

    return f"""## Job Description Analysis

**Role:** {role}
**Company Type:** {company_type}
**Experience Level:** {experience_level}

### Required Skills (by priority):
{skills_text}

### Engineering Expectations:
{expectations_text}

### Key Responsibilities:
{responsibilities_text}

---

## Candidate Resume:
{resume_text[:15000]}

---

Evaluate this candidate's fit for the role above. Return ONLY valid JSON."""


async def fitness_scorer_node(state: AgentState) -> dict:
    """Score a resume against a JD analysis using LLM."""
    logger.info("Running fitness scorer node")

    try:
        llm = get_llm(task=LLMTask.ANALYSIS)

        skill_profile = state.get("skill_profile") or {}
        skills = skill_profile.get("skills", [])
        experience_level = skill_profile.get("experience_level", "mid")
        expectations = skill_profile.get("engineering_expectations", [])
        responsibilities = skill_profile.get("key_responsibilities", [])

        prompt = _build_fitness_prompt(
            role=state.get("role", "Unknown Role"),
            company_type=state.get("company_type", "mid_level"),
            skills=skills,
            experience_level=experience_level,
            expectations=expectations,
            responsibilities=responsibilities,
            resume_text=state.get("resume_text", ""),
        )

        messages = [
            SystemMessage(content=FITNESS_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        # Attempt with retry
        for attempt in range(2):
            response = await llm.ainvoke(messages)
            raw = response.content.strip()

            # Strip markdown fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```\s*$", "", raw)

            try:
                result = json.loads(raw)
                break
            except json.JSONDecodeError:
                if attempt == 0:
                    messages.append(HumanMessage(
                        content="Your response was not valid JSON. Return ONLY a JSON object, no markdown fences or extra text."
                    ))
                    logger.warning("Fitness scorer: retrying due to invalid JSON")
                else:
                    logger.error("Fitness scorer: JSON parse failed after retry")
                    return {
                        "fitness_result": None,
                        "errors": (state.get("errors") or []) + ["Failed to parse fitness evaluation"],
                    }

        # Validate and normalize
        fitness_score = max(0, min(100, float(result.get("fitness_score", 0))))
        verdict = result.get("verdict", "weak_fit")
        if verdict not in ("strong_fit", "good_fit", "partial_fit", "weak_fit"):
            verdict = "partial_fit"

        fitness_result = {
            "fitness_score": fitness_score,
            "verdict": verdict,
            "matched_skills": result.get("matched_skills", [])[:20],
            "missing_skills": result.get("missing_skills", [])[:15],
            "strengths": result.get("strengths", [])[:10],
            "improvements": result.get("improvements", [])[:10],
            "detailed_feedback": str(result.get("detailed_feedback", ""))[:5000],
        }

        logger.info(f"Fitness evaluation complete: score={fitness_score}, verdict={verdict}")
        return {"fitness_result": fitness_result}

    except Exception as e:
        logger.error(f"Fitness scorer node failed: {e}", exc_info=True)
        return {
            "fitness_result": None,
            "errors": (state.get("errors") or []) + [f"Fitness evaluation failed: {str(e)[:200]}"],
        }
