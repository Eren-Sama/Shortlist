"""
Shortlist — Agent State Definition

Shared state schema for the LangGraph multi-agent pipeline.
All agent nodes read from and write to this state.
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Central state shared across all LangGraph nodes.

    Each field represents a data domain that flows through the pipeline.
    Nodes read what they need and write their outputs.
    """

    # ── User Input ──
    jd_text: str
    role: str
    company_type: str
    geography: Optional[str]

    # ── JD Analysis Output ──
    skill_profile: Optional[dict]          # Serialized SkillProfile
    engineering_expectations: Optional[list[dict]]

    # ── Company Logic Output ──
    company_modifiers: Optional[dict]      # Serialized CompanyModifiers

    # ── Capstone Generator Output ──
    generated_projects: Optional[list[dict]]  # List of serialized ProjectIdea

    # ── Repo Analyzer Output ──
    repo_url: Optional[str]
    repo_scorecard: Optional[dict]         # Serialized RepoScoreCard

    # ── Scaffold Input ──
    scaffold_project_title: Optional[str]
    scaffold_project_description: Optional[str]
    scaffold_tech_stack: Optional[list[str]]
    scaffold_options: Optional[dict]

    # ── Scaffold Output ──
    scaffold_files: Optional[list[dict]]
    scaffold_file_tree: Optional[str]
    scaffold_project_name: Optional[str]

    # ── Portfolio Input ──
    portfolio_project_title: Optional[str]
    portfolio_project_description: Optional[str]
    portfolio_tech_stack: Optional[list[str]]
    portfolio_key_features: Optional[list[str]]
    portfolio_repo_score: Optional[float]
    portfolio_target_role: Optional[str]

    # ── Portfolio Output ──
    portfolio_output: Optional[dict]

    # ── Resume Fitness Input ──
    resume_text: Optional[str]

    # ── Resume Fitness Output ──
    fitness_result: Optional[dict]

    # ── Agent Messages (for streaming / debugging) ──
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Metadata ──
    user_id: Optional[str]
    analysis_id: Optional[str]
    current_phase: Optional[str]
    errors: Optional[list[str]]
