"""
Shortlist — Pydantic Schemas: JD Analysis

Input/output models for the JD Intelligence Engine.
All user inputs are validated and constrained.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class CompanyType(str, Enum):
    STARTUP = "startup"
    MID_LEVEL = "mid_level"
    FAANG = "faang"
    RESEARCH = "research"
    ENTERPRISE = "enterprise"


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"


# ── Input Models ──

class JDAnalysisRequest(BaseModel):
    """User-submitted job description for analysis."""

    jd_text: str = Field(
        ...,
        min_length=50,
        max_length=15000,
        description="Full job description text",
    )
    role: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Target role (e.g., 'Backend Engineer', 'ML Engineer')",
    )
    company_type: CompanyType = Field(
        ...,
        description="Type of company",
    )
    company_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Company name (optional)",
    )
    geography: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Job location or geography (e.g., 'US', 'India', 'Remote')",
    )

    @field_validator("jd_text")
    @classmethod
    def sanitize_jd(cls, v: str) -> str:
        # Remove null bytes and excessive whitespace
        v = v.replace("\x00", "").strip()
        if len(v) < 50:
            raise ValueError("Job description must be at least 50 characters")
        return v


# ── Output Models ──

class Skill(BaseModel):
    """A single skill extracted from the JD with a priority weight."""

    name: str = Field(..., description="Skill name (e.g., 'Python', 'System Design')")
    category: str = Field(
        ..., description="Category: 'language', 'framework', 'concept', 'tool', 'soft_skill'"
    )
    weight: float = Field(
        ..., ge=0.0, le=10.0,
        description="Priority weight (0-10, higher = more important)",
    )
    source: str = Field(
        ..., description="Where this skill was found: 'required', 'preferred', 'inferred'"
    )


class EngineeringExpectation(BaseModel):
    """What the company expects from an engineering perspective."""

    dimension: str = Field(..., description="e.g., 'Scale', 'Clean Code', 'Shipping Speed'")
    importance: float = Field(..., ge=0.0, le=10.0)
    description: str = Field(..., max_length=500)


class SkillProfile(BaseModel):
    """Complete skill profile extracted from JD analysis."""

    skills: list[Skill] = Field(default_factory=list)
    experience_level: ExperienceLevel
    domain: str = Field(..., description="Primary domain (e.g., 'Backend', 'ML', 'Full-Stack')")
    engineering_expectations: list[EngineeringExpectation] = Field(default_factory=list)
    key_responsibilities: list[str] = Field(default_factory=list)
    summary: str = Field(..., max_length=8000, description="One-paragraph summary")


class CompanyModifiers(BaseModel):
    """Behavior modifiers based on company type."""

    company_type: CompanyType
    emphasis_areas: list[str] = Field(default_factory=list)
    weight_adjustments: dict[str, float] = Field(
        default_factory=dict,
        description="Skill name → weight adjustment (+/-)",
    )
    portfolio_focus: str = Field(..., description="What to emphasize in portfolio")


class JDAnalysisResponse(BaseModel):
    """Complete JD analysis output."""

    analysis_id: Optional[str] = None
    skill_profile: SkillProfile
    company_modifiers: CompanyModifiers
    raw_role: str
    raw_company_type: CompanyType
    raw_geography: Optional[str] = None
