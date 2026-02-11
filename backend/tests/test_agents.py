"""
Shortlist — Agent Node Tests

Tests for the LangGraph agent nodes with mocked LLM responses.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.state import AgentState


def _make_base_state(**overrides) -> AgentState:
    """Create a base AgentState with sensible defaults."""
    state: AgentState = {
        "jd_text": "",
        "role": "Backend Engineer",
        "company_type": "startup",
        "geography": None,
        "skill_profile": None,
        "engineering_expectations": None,
        "company_modifiers": None,
        "generated_projects": None,
        "repo_url": None,
        "repo_scorecard": None,
        "scaffold_files": None,
        "portfolio_output": None,
        "messages": [],
        "user_id": "test-user-id",
        "analysis_id": "test-analysis-id",
        "current_phase": "jd_analysis",
        "errors": [],
    }
    state.update(overrides)
    return state


class TestJDNode:
    """Tests for the JD analysis agent node."""

    @pytest.mark.asyncio
    async def test_jd_node_extracts_skills(self):
        """JD node should extract skills from job description text."""
        mock_llm_response = MagicMock()
        mock_llm_response.content = '''{
            "primary_skills": [
                {"name": "Python", "category": "language", "weight": 9, "source": "explicit"},
                {"name": "FastAPI", "category": "framework", "weight": 8, "source": "explicit"}
            ],
            "secondary_skills": [
                {"name": "Docker", "category": "devops", "weight": 5, "source": "explicit"}
            ],
            "inferred_skills": [],
            "experience_level": "senior",
            "domain_keywords": ["microservices", "backend"]
        }'''

        with patch("app.agents.nodes.jd_node.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_llm_response
            mock_get_llm.return_value = mock_llm

            from app.agents.nodes.jd_node import jd_analysis_node

            state = _make_base_state(
                jd_text="Senior Python Backend Engineer with 5+ years experience in FastAPI and Docker."
            )
            result = await jd_analysis_node(state)

            assert result["skill_profile"] is not None
            assert result["current_phase"] == "jd_analysis_complete"
            assert "errors" not in result or len(result.get("errors", [])) == 0

    @pytest.mark.asyncio
    async def test_jd_node_handles_llm_error(self):
        """JD node should gracefully handle LLM failures."""
        with patch("app.agents.nodes.jd_node.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("LLM service unavailable")
            mock_get_llm.return_value = mock_llm

            from app.agents.nodes.jd_node import jd_analysis_node

            state = _make_base_state(
                jd_text="Python Backend Engineer needed for high-scale distributed system."
            )
            result = await jd_analysis_node(state)

            assert len(result["errors"]) > 0
            assert "failed" in result["errors"][0].lower()


class TestCompanyNode:
    """Tests for the company logic node (deterministic, no LLM)."""

    @pytest.mark.asyncio
    async def test_startup_modifiers_applied(self):
        """Startup company type should emphasize speed and shipping."""
        from app.agents.nodes.company_node import company_logic_node

        state = _make_base_state(
            company_type="startup",
            skill_profile={
                "primary_skills": [
                    {"name": "Python", "category": "language", "weight": 7, "source": "explicit"},
                ],
                "secondary_skills": [],
                "inferred_skills": [],
                "experience_level": "mid",
                "domain_keywords": [],
            },
        )
        result = await company_logic_node(state)

        assert result["company_modifiers"] is not None
        assert result["current_phase"] == "company_logic_complete"

    @pytest.mark.asyncio
    async def test_faang_modifiers_applied(self):
        """FAANG company type should emphasize system design and scale."""
        from app.agents.nodes.company_node import company_logic_node

        state = _make_base_state(
            company_type="faang",
            skill_profile={
                "primary_skills": [
                    {"name": "Python", "category": "language", "weight": 7, "source": "explicit"},
                    {"name": "System Design", "category": "architecture", "weight": 8, "source": "explicit"},
                ],
                "secondary_skills": [],
                "inferred_skills": [],
                "experience_level": "senior",
                "domain_keywords": [],
            },
        )
        result = await company_logic_node(state)

        assert result["company_modifiers"] is not None
        assert result["current_phase"] == "company_logic_complete"

    @pytest.mark.asyncio
    async def test_missing_skill_profile_handled_gracefully(self):
        """Company node should handle missing skill profile gracefully."""
        from app.agents.nodes.company_node import company_logic_node

        state = _make_base_state(skill_profile=None)
        result = await company_logic_node(state)

        assert result["company_modifiers"] is not None
        assert result["current_phase"] == "company_logic_complete"
        assert result["skill_profile"] == {}


class TestCapstoneNode:
    """Tests for the capstone project generator node."""

    @pytest.mark.asyncio
    async def test_capstone_generates_projects(self):
        """Capstone node should generate project ideas from skill profile."""
        mock_llm_response = MagicMock()
        mock_llm_response.content = '''{
            "projects": [
                {
                    "title": "Real-time API Gateway",
                    "problem_statement": "Build a high-performance API gateway with rate limiting",
                    "architecture": "Microservice with Redis cache and PostgreSQL storage",
                    "tech_stack": ["Python", "FastAPI", "Redis", "PostgreSQL"],
                    "complexity": 4,
                    "resume_bullet": "Designed a real-time API gateway handling 10K req/s",
                    "differentiator": "Custom rate-limiting algorithm with sliding window"
                }
            ]
        }'''

        with patch("app.agents.nodes.capstone_node.get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_llm_response
            mock_get_llm.return_value = mock_llm

            from app.agents.nodes.capstone_node import capstone_generator_node

            state = _make_base_state(
                skill_profile={
                    "primary_skills": [
                        {"name": "Python", "category": "language", "weight": 9, "source": "explicit"},
                    ],
                    "secondary_skills": [],
                    "inferred_skills": [],
                    "experience_level": "senior",
                    "domain_keywords": ["backend", "distributed"],
                },
                company_modifiers={
                    "company_type": "startup",
                    "emphasis_areas": ["speed", "shipping"],
                    "weight_adjustments": {},
                    "portfolio_focus": "demo-heavy",
                },
            )
            result = await capstone_generator_node(state)

            assert result["generated_projects"] is not None
            assert result["current_phase"] == "capstone_generation_complete"
