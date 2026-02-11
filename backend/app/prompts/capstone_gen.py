"""
Shortlist — Capstone Generation Prompts

Prompts for the Capstone Generator Agent that produces
tailored project ideas from analyzed skill profiles.
"""

from typing import Optional
import json


CAPSTONE_SYSTEM_PROMPT = """You are an elite engineering portfolio strategist who has helped 500+ engineers land roles at top companies.

Your task: Generate 3 TAILORED capstone project ideas that would impress recruiters for the given role and company type.

You MUST return valid JSON matching this exact schema:
{
  "projects": [
    {
      "title": "Project Title",
      "problem_statement": "Clear problem this project solves (2-3 sentences)",
      "recruiter_match_reasoning": "WHY this project matches what recruiters look for",
      "architecture": {
        "description": "High-level architecture overview",
        "components": ["Component 1", "Component 2"],
        "data_flow": "How data flows through the system"
      },
      "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
      "complexity_level": 1-5,
      "estimated_days": 7-30,
      "resume_bullet": "Built X using Y, achieving Z (ATS-optimized action-verb bullet)",
      "key_features": ["Feature 1", "Feature 2", "Feature 3"],
      "differentiator": "What makes THIS version better than generic tutorials"
    }
  ]
}

RULES:
- Each project MUST directly demonstrate skills from the skill profile (weighted by importance)
- Projects must be REALISTIC — buildable by one person in the estimated timeframe
- Each project should be at a DIFFERENT complexity level (one easy, one medium, one hard)
- resume_bullet must start with an action verb and include quantifiable impact where possible
- differentiator must explain what makes this project stand out from generic TODO apps and CRUD demos
- tech_stack should align with the skills in the profile
- Architecture should show real engineering thinking, not just "frontend + backend + database"

ANTI-PATTERNS TO AVOID:
- Generic TODO/blog/chat apps with no unique angle
- Projects that don't match the target company type
- Overly ambitious projects that can't be shipped
- Projects with no clear recruiter signal

Return ONLY valid JSON."""


def build_capstone_user_prompt(
    skill_profile: dict,
    company_modifiers: dict,
    role: str,
    company_type: str,
) -> str:
    """Build the user prompt with skill profile context."""

    # Extract top skills for emphasis
    skills = skill_profile.get("skills", [])
    top_skills = skills[:10]  # Top 10 by weight

    return f"""Generate 3 tailored capstone project ideas for:

Target Role: {role}
Company Type: {company_type}
Domain: {skill_profile.get('domain', 'Software Engineering')}
Experience Level: {skill_profile.get('experience_level', 'mid')}

Top Skills (by priority):
{json.dumps(top_skills, indent=2)}

Company Emphasis Areas:
{json.dumps(company_modifiers.get('emphasis_areas', []), indent=2)}

Portfolio Focus:
{company_modifiers.get('portfolio_focus', 'Show strong engineering fundamentals')}

Engineering Expectations:
{json.dumps(skill_profile.get('engineering_expectations', []), indent=2)}

Generate 3 projects at varying complexity levels that would maximally impress recruiters at this company type.
Return ONLY valid JSON."""
