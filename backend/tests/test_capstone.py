"""
Shortlist — Capstone Generator Tests

Tests for capstone generation: prompts, node, API, schemas.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Schema Tests

class TestCapstoneSchemas:
    """Test Pydantic schema validation for capstone models."""

    def test_project_idea_valid(self):
        from app.schemas.capstone import ProjectIdea, ArchitectureOverview
        idea = ProjectIdea(
            title="Real-time Chat API",
            problem_statement="Build a scalable WebSocket chat backend.",
            recruiter_match_reasoning="Shows distributed systems skills.",
            architecture=ArchitectureOverview(
                description="Event-driven microservice",
                components=["API Gateway", "Message Broker"],
                data_flow="Client → WS Gateway → Redis Pub/Sub → Consumers",
            ),
            tech_stack=["Python", "FastAPI", "Redis", "PostgreSQL"],
            complexity_level=3,
            estimated_days=14,
            resume_bullet="Built real-time chat API handling 10K concurrent connections using WebSockets and Redis Pub/Sub",
            key_features=["Room management", "Typing indicators"],
            differentiator="Production-grade connection management with graceful reconnection",
        )
        assert idea.complexity_level == 3
        assert len(idea.tech_stack) == 4

    def test_project_idea_complexity_range(self):
        from app.schemas.capstone import ProjectIdea, ArchitectureOverview
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectIdea(
                title="Test",
                problem_statement="Test",
                recruiter_match_reasoning="Test",
                architecture=ArchitectureOverview(
                    description="Test", components=[], data_flow="Test"
                ),
                tech_stack=[],
                complexity_level=6,  # out of range
                estimated_days=14,
                resume_bullet="Test",
                key_features=[],
                differentiator="Test",
            )

    def test_capstone_request_defaults(self):
        from app.schemas.capstone import CapstoneGenerationRequest
        req = CapstoneGenerationRequest(analysis_id="abc-123")
        assert req.num_projects == 3
        assert req.preferred_stack is None

    def test_capstone_request_custom(self):
        from app.schemas.capstone import CapstoneGenerationRequest
        req = CapstoneGenerationRequest(
            analysis_id="abc-123",
            num_projects=5,
            preferred_stack=["Go", "gRPC"],
        )
        assert req.num_projects == 5
        assert "Go" in req.preferred_stack

# Prompt Tests

class TestCapstonePrompts:
    """Test capstone prompt generation."""

    def test_system_prompt_exists(self):
        from app.prompts.capstone_gen import CAPSTONE_SYSTEM_PROMPT
        assert "capstone" in CAPSTONE_SYSTEM_PROMPT.lower() or "project" in CAPSTONE_SYSTEM_PROMPT.lower()
        assert "JSON" in CAPSTONE_SYSTEM_PROMPT

    def test_build_user_prompt(self):
        from app.prompts.capstone_gen import build_capstone_user_prompt
        prompt = build_capstone_user_prompt(
            skill_profile={
                "skills": [
                    {"name": "Python", "weight": 9},
                    {"name": "FastAPI", "weight": 8},
                ],
                "domain": "Backend Engineering",
                "experience_level": "senior",
                "engineering_expectations": ["Scalability", "Testing"],
            },
            company_modifiers={
                "emphasis_areas": ["System Design", "Testing"],
                "portfolio_focus": "Demonstrate distributed systems expertise",
            },
            role="Senior Backend Engineer",
            company_type="faang",
        )
        assert "Senior Backend Engineer" in prompt
        assert "faang" in prompt
        assert "Python" in prompt

    def test_build_user_prompt_minimal(self):
        from app.prompts.capstone_gen import build_capstone_user_prompt
        prompt = build_capstone_user_prompt(
            skill_profile={},
            company_modifiers={},
            role="SWE",
            company_type="startup",
        )
        assert "SWE" in prompt
        assert "startup" in prompt

# Capstone Node Tests

class TestCapstoneNode:
    """Test the capstone_generator_node."""

    @pytest.fixture
    def mock_capstone_llm_response(self):
        projects_json = json.dumps({
            "projects": [
                {
                    "title": "Real-time Analytics Dashboard",
                    "problem_statement": "Build a real-time data visualization platform.",
                    "recruiter_match_reasoning": "Shows full-stack + data engineering.",
                    "architecture": {
                        "description": "Event-driven with streaming pipeline",
                        "components": ["API", "Stream Processor", "Dashboard"],
                        "data_flow": "Sources → Kafka → Flink → API → React",
                    },
                    "tech_stack": ["Python", "React", "Apache Kafka"],
                    "complexity_level": 4,
                    "estimated_days": 21,
                    "resume_bullet": "Built real-time analytics platform processing 100K events/sec",
                    "key_features": ["Live charts", "Alert rules"],
                    "differentiator": "Production-grade streaming pipeline, not just a chart demo",
                },
            ]
        })
        mock_resp = MagicMock()
        mock_resp.content = projects_json
        return mock_resp

    @pytest.mark.asyncio
    async def test_capstone_node_success(self, mock_capstone_llm_response):
        from app.agents.nodes.capstone_node import capstone_generator_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_capstone_llm_response)

        state = {
            "skill_profile": {"skills": [{"name": "Python", "weight": 9}]},
            "company_modifiers": {"emphasis_areas": ["Testing"]},
            "role": "Backend Engineer",
            "company_type": "startup",
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.capstone_node.get_llm", return_value=mock_llm):
            result = await capstone_generator_node(state)

        assert result["current_phase"] == "capstone_generation_complete"
        assert len(result["generated_projects"]) == 1
        assert result["generated_projects"][0]["title"] == "Real-time Analytics Dashboard"

    @pytest.mark.asyncio
    async def test_capstone_node_invalid_json(self):
        from app.agents.nodes.capstone_node import capstone_generator_node

        mock_resp = MagicMock()
        mock_resp.content = "Not valid JSON"
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

        state = {
            "skill_profile": {},
            "company_modifiers": {},
            "role": "SWE",
            "company_type": "startup",
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.capstone_node.get_llm", return_value=mock_llm):
            result = await capstone_generator_node(state)

        # Should still succeed but with empty projects
        assert result["current_phase"] == "capstone_generation_complete"
        assert result["generated_projects"] == []

    @pytest.mark.asyncio
    async def test_capstone_node_exception(self):
        from app.agents.nodes.capstone_node import capstone_generator_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("LLM error"))

        state = {
            "skill_profile": {},
            "company_modifiers": {},
            "role": "SWE",
            "company_type": "startup",
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.capstone_node.get_llm", return_value=mock_llm):
            result = await capstone_generator_node(state)

        assert "capstone_generation_failed" in result["current_phase"]
        assert len(result["errors"]) > 0

# API Tests

class TestCapstoneAPI:
    """Test capstone API endpoints."""

    def test_capstone_generate_requires_auth(self, client):
        response = client.post(
            "/api/v1/capstone/generate",
            json={"analysis_id": "some-id"},
        )
        assert response.status_code in (401, 403)

    def test_capstone_get_requires_auth(self, client):
        response = client.get("/api/v1/capstone/some-id")
        assert response.status_code in (401, 403)

    def test_capstone_select_requires_auth(self, client):
        response = client.put("/api/v1/capstone/some-id/select?selected=true")
        assert response.status_code in (401, 403)

    def test_capstone_safe_parse(self):
        """Test the _safe_parse_project helper."""
        from app.api.v1.capstone import _safe_parse_project

        raw = {
            "title": "Test Project",
            "problem_statement": "Test problem",
            "recruiter_match_reasoning": "Test reasoning",
            "architecture": {
                "description": "Test arch",
                "components": ["A", "B"],
                "data_flow": "A → B",
            },
            "tech_stack": ["Python"],
            "complexity_level": 3,
            "estimated_days": 14,
            "resume_bullet": "Built X using Y, achieving Z",
            "key_features": ["Feature 1"],
            "differentiator": "Better than average",
        }
        parsed = _safe_parse_project(raw)
        assert parsed.title == "Test Project"
        assert parsed.complexity_level == 3

    def test_capstone_safe_parse_string_architecture(self):
        """Handle architecture as plain string."""
        from app.api.v1.capstone import _safe_parse_project

        raw = {
            "title": "Test",
            "problem_statement": "Test",
            "recruiter_match_reasoning": "Test",
            "architecture": "Simple monolith",
            "tech_stack": [],
            "complexity_level": 2,
            "estimated_days": 7,
            "resume_bullet": "Test",
            "key_features": [],
            "differentiator": "Test",
        }
        parsed = _safe_parse_project(raw)
        assert parsed.architecture.description == "Simple monolith"
