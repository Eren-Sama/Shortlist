"""
Shortlist — Pydantic Schemas: Capstone Projects

Models for the Capstone Generator Agent output.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ArchitectureOverview(BaseModel):
    """High-level architecture description for a project idea."""

    description: str = Field(..., max_length=2000)
    components: list[str] = Field(default_factory=list, description="Major system components")
    data_flow: str = Field(..., max_length=1000, description="How data flows through the system")
    diagram_mermaid: Optional[str] = Field(
        default=None,
        max_length=3000,
        description="Mermaid.js diagram code",
    )


class ProjectIdea(BaseModel):
    """A single generated capstone project idea."""

    title: str = Field(..., max_length=200)
    problem_statement: str = Field(..., max_length=1500)
    recruiter_match_reasoning: str = Field(
        ..., max_length=1000,
        description="Why this project matches the recruiter's expectations",
    )
    architecture: ArchitectureOverview
    tech_stack: list[str] = Field(default_factory=list)
    complexity_level: int = Field(..., ge=1, le=5, description="1=Easy, 5=Expert")
    estimated_days: int = Field(..., ge=1, le=90)
    resume_bullet: str = Field(
        ..., max_length=300,
        description="ATS-optimized resume bullet for this project",
    )
    key_features: list[str] = Field(default_factory=list)
    differentiator: str = Field(
        ..., max_length=500,
        description="What makes this project stand out from generic versions",
    )


class CapstoneGenerationRequest(BaseModel):
    """Request to generate capstone projects from a JD analysis."""

    analysis_id: str = Field(..., description="ID of the JD analysis to base generation on")
    num_projects: int = Field(default=3, ge=1, le=5)
    preferred_stack: Optional[list[str]] = Field(
        default=None,
        description="Optional: preferred technologies to include",
    )


class CapstoneGenerationResponse(BaseModel):
    """Generated capstone project ideas."""

    analysis_id: str
    projects: list[ProjectIdea]
    generation_metadata: dict = Field(
        default_factory=dict,
        description="Model used, tokens consumed, etc.",
    )
