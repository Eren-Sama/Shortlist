"""
Shortlist — Pydantic Schemas: Resume Fitness Scorer

Models for the JD + Resume fit evaluation feature.
"""

from pydantic import BaseModel, Field
from typing import Optional


class MatchedSkill(BaseModel):
    """A skill from the JD that the candidate demonstrates."""
    name: str
    evidence: str = Field(..., max_length=300)


class MissingSkill(BaseModel):
    """A skill from the JD the candidate lacks."""
    name: str
    importance: str = Field(..., description="critical | important | nice_to_have")
    suggestion: str = Field(..., max_length=500)


class Improvement(BaseModel):
    """An actionable improvement recommendation."""
    area: str
    current_state: str = Field(default="", max_length=500, description="What the resume currently shows")
    recommended_action: str = Field(default="", max_length=500, description="Specific actionable step")
    impact: str = Field(default="medium", description="high | medium | low")


class FitnessScoreRequest(BaseModel):
    """Request to score a resume against a JD analysis."""
    analysis_id: str = Field(..., description="ID of the JD analysis to compare against")
    resume_text: str = Field(
        ...,
        min_length=50,
        max_length=30000,
        description="Full resume text (extracted from PDF or pasted)",
    )


class FitnessScoreResponse(BaseModel):
    """Complete fitness evaluation result."""
    id: str
    analysis_id: str
    fitness_score: float = Field(..., ge=0, le=100)
    verdict: str = Field(..., description="strong_fit | good_fit | partial_fit | weak_fit")
    matched_skills: list[MatchedSkill] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[Improvement] = Field(default_factory=list)
    detailed_feedback: str = Field(..., max_length=5000)
    role: str
    company_type: str
    processing_time_ms: int


class FitnessListItem(BaseModel):
    """Summary item for listing fitness scores."""
    id: str
    analysis_id: str
    role: Optional[str] = None
    company_type: Optional[str] = None
    fitness_score: Optional[float] = None
    verdict: Optional[str] = None
    status: str
    created_at: str
