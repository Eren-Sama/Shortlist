"""
Shortlist — Pydantic Schemas: Portfolio Optimizer

Models for README, resume bullets, demo scripts, and LinkedIn posts.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app.security import sanitize_string


class PortfolioOptimizeRequest(BaseModel):
    """Request to generate optimized portfolio materials."""

    project_title: str = Field(..., min_length=3, max_length=200)
    project_description: str = Field(..., min_length=20, max_length=3000)
    tech_stack: list[str] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list)
    repo_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0,
        description="Overall repo score (if available from analysis)",
    )
    target_role: Optional[str] = Field(default=None, max_length=200)
    analysis_id: Optional[str] = None

    @field_validator("project_title", "project_description")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        return sanitize_string(v)


class ResumeBullet(BaseModel):
    """A single ATS-optimized resume bullet."""

    bullet: str = Field(..., max_length=300)
    keywords: list[str] = Field(default_factory=list, description="ATS keywords in the bullet")
    impact_type: str = Field(
        ..., description="Type of impact: 'quantitative', 'qualitative', 'technical'"
    )


class DemoScript(BaseModel):
    """Step-by-step demo narration script."""

    total_duration_seconds: int = Field(default=120)
    steps: list[dict] = Field(
        default_factory=list,
        description="List of {timestamp, action, narration} dicts",
    )
    opening_hook: str = Field(..., max_length=500)
    closing_cta: str = Field(..., max_length=300)


class LinkedInPost(BaseModel):
    """LinkedIn announcement post."""

    hook: str = Field(..., max_length=200, description="First line — attention grabber")
    body: str = Field(..., max_length=2000)
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = Field(..., max_length=200)


class PortfolioOptimizeResponse(BaseModel):
    """Complete portfolio optimization output."""

    readme_markdown: str = Field(..., description="Full polished README.md content")
    resume_bullets: list[ResumeBullet]
    demo_script: DemoScript
    linkedin_post: LinkedInPost
    generation_metadata: dict = Field(default_factory=dict)
