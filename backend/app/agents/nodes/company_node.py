"""
Shortlist — Company Logic Node

Applies company-type behavior modifiers to the skill profile.
Adjusts skill weights based on what different company archetypes value.
"""

from app.agents.state import AgentState
from app.logging_config import get_logger

logger = get_logger("agents.company_node")

# Company-Type Modifier Rules
# Hardcoded for determinism — no LLM variance here.
COMPANY_MODIFIERS = {
    "startup": {
        "emphasis_areas": [
            "Shipping speed", "Full-stack capability", "MVP mindset",
            "Wearing multiple hats", "Rapid iteration",
        ],
        "weight_adjustments": {
            "full-stack": +3.0,
            "shipping speed": +3.0,
            "react": +1.5,
            "fastapi": +1.5,
            "docker": +2.0,
            "ci/cd": +1.5,
            "system design": -1.0,
        },
        "portfolio_focus": (
            "Show end-to-end projects shipped solo. "
            "Emphasize speed, deployment, and user-facing features."
        ),
    },
    "mid_level": {
        "emphasis_areas": [
            "Clean architecture", "Code quality", "Testing",
            "Design patterns", "Team collaboration",
        ],
        "weight_adjustments": {
            "clean code": +3.0,
            "testing": +2.5,
            "design patterns": +2.0,
            "code review": +1.5,
            "documentation": +1.5,
        },
        "portfolio_focus": (
            "Show well-structured projects with tests, CI, and clean code. "
            "Emphasize maintainability, modularity, and code quality metrics."
        ),
    },
    "faang": {
        "emphasis_areas": [
            "System design", "Scalability", "Data structures & algorithms",
            "Distributed systems", "Performance optimization",
        ],
        "weight_adjustments": {
            "system design": +4.0,
            "scalability": +3.5,
            "algorithms": +3.0,
            "distributed systems": +2.5,
            "performance": +2.0,
            "kubernetes": +1.5,
        },
        "portfolio_focus": (
            "Show projects that demonstrate scale thinking. "
            "Include architecture diagrams, load considerations, "
            "and system design documentation."
        ),
    },
    "research": {
        "emphasis_areas": [
            "Novel approach", "Rigorous evaluation", "Paper-grade documentation",
            "Reproducibility", "Experiment tracking",
        ],
        "weight_adjustments": {
            "machine learning": +3.0,
            "evaluation metrics": +2.5,
            "reproducibility": +2.0,
            "research methodology": +2.0,
            "python": +1.0,
        },
        "portfolio_focus": (
            "Show projects with clear problem formulation, novel approaches, "
            "ablation studies, and paper-quality writeups."
        ),
    },
    "enterprise": {
        "emphasis_areas": [
            "Security", "Reliability", "Compliance",
            "Error handling", "Logging & monitoring", "Documentation",
        ],
        "weight_adjustments": {
            "security": +4.0,
            "reliability": +3.0,
            "error handling": +2.5,
            "logging": +2.0,
            "monitoring": +2.0,
            "documentation": +2.0,
            "compliance": +1.5,
        },
        "portfolio_focus": (
            "Show projects with robust error handling, security headers, "
            "structured logging, auth, and deployment pipelines."
        ),
    },
}

async def company_logic_node(state: AgentState) -> dict:
    """
    Company Logic Agent Node.

    Applies deterministic company-type modifiers to the skill profile.
    No LLM call needed — rules are explicit and auditable.

    Input (from state):
        - company_type: The company archetype
        - skill_profile: Extracted skills from JD analysis

    Output (to state):
        - company_modifiers: Applied modifiers
        - skill_profile: Updated with adjusted weights
    """
    company_type = state.get("company_type", "mid_level").lower()

    logger.info(f"Applying company modifiers for: {company_type}")

    modifiers = COMPANY_MODIFIERS.get(company_type, COMPANY_MODIFIERS["mid_level"])

    # Apply weight adjustments to skill profile
    skill_profile = state.get("skill_profile") or {}
    if not skill_profile:
        logger.warning("No skill profile available — returning modifiers without weight adjustments")
        return {
            "skill_profile": {},
            "company_modifiers": {
                "company_type": company_type,
                "emphasis_areas": modifiers["emphasis_areas"],
                "weight_adjustments": modifiers["weight_adjustments"],
                "portfolio_focus": modifiers["portfolio_focus"],
            },
            "current_phase": "company_logic_complete",
            "messages": [],
        }

    skills = skill_profile.get("skills", [])

    adjustments = modifiers["weight_adjustments"]
    for skill in skills:
        skill_name_lower = skill.get("name", "").lower()
        for adj_key, adj_value in adjustments.items():
            if adj_key in skill_name_lower:
                original = skill.get("weight", 5.0)
                adjusted = max(0.0, min(10.0, original + adj_value))
                skill["weight"] = adjusted
                logger.debug(
                    f"Adjusted '{skill['name']}': {original:.1f} → {adjusted:.1f} "
                    f"(company modifier: {adj_key} {adj_value:+.1f})"
                )

    # Sort skills by weight (highest first)
    skills.sort(key=lambda s: s.get("weight", 0), reverse=True)
    skill_profile["skills"] = skills

    company_modifier_output = {
        "company_type": company_type,
        "emphasis_areas": modifiers["emphasis_areas"],
        "weight_adjustments": modifiers["weight_adjustments"],
        "portfolio_focus": modifiers["portfolio_focus"],
    }

    logger.info(f"Company modifiers applied: {len(modifiers['emphasis_areas'])} emphasis areas")

    return {
        "skill_profile": skill_profile,
        "company_modifiers": company_modifier_output,
        "current_phase": "company_logic_complete",
        "messages": [],
    }
