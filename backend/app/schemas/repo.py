"""
Shortlist — Pydantic Schemas: Repo Analysis

Models for the GitHub Repo Analyzer scoring engine.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class RepoAnalysisRequest(BaseModel):
    """Request to analyze a GitHub repository."""

    github_url: str = Field(
        ...,
        max_length=500,
        description="GitHub repository URL (https://github.com/owner/repo)",
    )

    @field_validator("github_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        pattern = r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+/?$"
        if not re.match(pattern, v):
            raise ValueError(
                "Must be a valid GitHub URL: https://github.com/{owner}/{repo}"
            )
        return v


class ScoreDimension(BaseModel):
    """A single scoring dimension with score and details."""

    name: str
    score: float = Field(..., ge=0.0, le=10.0)
    details: str = Field(..., max_length=1000)
    suggestions: list[str] = Field(default_factory=list)


class RepoScoreCard(BaseModel):
    """Complete recruiter scorecard for a repository."""

    repo_url: str
    repo_name: str
    primary_language: Optional[str] = None
    total_files: int = 0
    total_lines: int = 0

    code_quality: ScoreDimension
    test_coverage: ScoreDimension
    complexity: ScoreDimension
    structure: ScoreDimension
    deployment_readiness: ScoreDimension

    overall_score: float = Field(..., ge=0.0, le=10.0)
    summary: str = Field(..., max_length=2000)
    top_improvements: list[str] = Field(default_factory=list, max_length=10)


class RepoAnalysisResponse(BaseModel):
    """Response from repo analysis endpoint."""

    analysis_id: Optional[str] = None
    scorecard: RepoScoreCard
    analysis_metadata: dict = Field(default_factory=dict)
