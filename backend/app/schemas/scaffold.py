"""
Shortlist — Pydantic Schemas: Scaffold Generator

Models for the repository scaffold generation system.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app.security import sanitize_string


class GeneratedFile(BaseModel):
    """A single file in the scaffolded repository."""

    path: str = Field(..., description="Relative file path (e.g., 'backend/main.py')")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="File language for syntax highlighting")
    description: str = Field(..., max_length=300, description="What this file does")


class ScaffoldRequest(BaseModel):
    """Request to scaffold a project repository."""

    project_title: str = Field(..., min_length=3, max_length=200)
    project_description: str = Field(..., min_length=20, max_length=2000)
    tech_stack: list[str] = Field(default_factory=list)
    include_docker: bool = Field(default=True)
    include_ci: bool = Field(default=True)
    include_tests: bool = Field(default=True)
    analysis_id: Optional[str] = Field(
        default=None,
        description="Link to a JD analysis for context-aware scaffolding",
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Link to a capstone project for direct scaffolding",
    )

    @field_validator("project_title", "project_description")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        return sanitize_string(v)


class ScaffoldResponse(BaseModel):
    """Generated scaffold output."""

    project_name: str
    files: list[GeneratedFile]
    file_tree: str = Field(..., description="ASCII file tree representation")
    download_url: Optional[str] = Field(
        default=None,
        description="URL to download the scaffold as a ZIP",
    )
    generation_metadata: dict = Field(default_factory=dict)
