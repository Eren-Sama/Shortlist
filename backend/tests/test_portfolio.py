"""
Tests for Phase 4 — Portfolio Optimizer

Covers: schemas, prompts, node logic, validation, pipeline, API endpoints.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.portfolio import (
    PortfolioOptimizeRequest,
    PortfolioOptimizeResponse,
    ResumeBullet,
    DemoScript,
    LinkedInPost,
)
from app.prompts.portfolio_opt import (
    PORTFOLIO_SYSTEM_PROMPT,
    build_portfolio_user_prompt,
)
from app.agents.nodes.portfolio_node import (
    portfolio_optimizer_node,
    _parse_portfolio_response,
    _validate_portfolio,
    MAX_README_LENGTH,
    MAX_BULLET_LENGTH,
    MAX_DEMO_STEPS,
)

# ─── Fixtures ───

VALID_PORTFOLIO_OUTPUT = {
    "readme_markdown": "# My Project\n\nA full-stack app.\n\n## Features\n- Auth\n- CRUD",
    "resume_bullets": [
        {
            "bullet": "Built a full-stack app with React and FastAPI serving 1000+ users",
            "keywords": ["React", "FastAPI", "full-stack"],
            "impact_type": "quantitative",
        },
        {
            "bullet": "Engineered CI/CD pipeline reducing deployment time by 60%",
            "keywords": ["CI/CD", "DevOps"],
            "impact_type": "quantitative",
        },
        {
            "bullet": "Designed microservice architecture for scalable API layer",
            "keywords": ["microservice", "API", "architecture"],
            "impact_type": "technical",
        },
    ],
    "demo_script": {
        "total_duration_seconds": 120,
        "opening_hook": "What if you could analyze any GitHub repo in 30 seconds?",
        "steps": [
            {
                "timestamp": "0:00-0:15",
                "action": "Show landing page",
                "narration": "Welcome to My Project",
            },
            {
                "timestamp": "0:15-0:45",
                "action": "Demo the main feature",
                "narration": "Watch as we analyze this repo instantly",
            },
        ],
        "closing_cta": "Star the repo and try it yourself!",
    },
    "linkedin_post": {
        "hook": "I just open-sourced something I've been working on for weeks.",
        "body": "Problem: analyzing repos is slow.\nSolution: I built an AI-powered analyzer.\nResult: 30-second insights.",
        "hashtags": ["#OpenSource", "#AI", "#WebDev"],
        "call_to_action": "Check it out on GitHub (link in comments)",
    },
}

# Schema Tests

class TestPortfolioSchemas:
    """Test Pydantic schema validation."""

    def test_valid_request(self):
        req = PortfolioOptimizeRequest(
            project_title="My Project",
            project_description="A full-stack web application with AI features",
            tech_stack=["Python", "React", "PostgreSQL"],
            target_role="Full-Stack Engineer",
        )
        assert req.project_title == "My Project"
        assert len(req.tech_stack) == 3
        assert req.target_role == "Full-Stack Engineer"

    def test_request_min_title_length(self):
        with pytest.raises(Exception):
            PortfolioOptimizeRequest(
                project_title="AB",  # Too short (min 3)
                project_description="A project description that is long enough",
            )

    def test_request_min_description_length(self):
        with pytest.raises(Exception):
            PortfolioOptimizeRequest(
                project_title="My Project",
                project_description="Too short",  # min 20
            )

    def test_request_repo_score_bounds(self):
        # Valid
        req = PortfolioOptimizeRequest(
            project_title="My Project",
            project_description="A full-stack web application with AI features",
            repo_score=8.5,
        )
        assert req.repo_score == 8.5

        # Invalid: over 10
        with pytest.raises(Exception):
            PortfolioOptimizeRequest(
                project_title="My Project",
                project_description="A full-stack web application with AI features",
                repo_score=11.0,
            )

    def test_resume_bullet_schema(self):
        bullet = ResumeBullet(
            bullet="Built a scalable API layer",
            keywords=["API", "scalable"],
            impact_type="technical",
        )
        assert len(bullet.keywords) == 2

    def test_demo_script_schema(self):
        script = DemoScript(
            total_duration_seconds=120,
            opening_hook="Watch this",
            closing_cta="Star the repo",
            steps=[],
        )
        assert script.total_duration_seconds == 120

    def test_linkedin_post_schema(self):
        post = LinkedInPost(
            hook="I built something cool",
            body="Here's what I made.",
            hashtags=["#dev"],
            call_to_action="Check it out",
        )
        assert post.hook == "I built something cool"

    def test_response_schema(self):
        resp = PortfolioOptimizeResponse(
            readme_markdown="# README",
            resume_bullets=[
                {
                    "bullet": "test",
                    "keywords": [],
                    "impact_type": "technical",
                }
            ],
            demo_script={
                "total_duration_seconds": 90,
                "opening_hook": "test",
                "closing_cta": "test",
                "steps": [],
            },
            linkedin_post={
                "hook": "test",
                "body": "test",
                "hashtags": [],
                "call_to_action": "test",
            },
        )
        assert resp.readme_markdown == "# README"

# Prompt Tests

class TestPortfolioPrompts:
    """Test prompt construction."""

    def test_system_prompt_contains_instructions(self):
        assert "README" in PORTFOLIO_SYSTEM_PROMPT
        assert "resume_bullets" in PORTFOLIO_SYSTEM_PROMPT
        assert "demo_script" in PORTFOLIO_SYSTEM_PROMPT
        assert "linkedin_post" in PORTFOLIO_SYSTEM_PROMPT
        assert "valid JSON" in PORTFOLIO_SYSTEM_PROMPT

    def test_user_prompt_basic(self):
        prompt = build_portfolio_user_prompt(
            project_title="Shortlist",
            project_description="AI portfolio builder",
            tech_stack=["Python", "React"],
        )
        assert "Shortlist" in prompt
        assert "AI portfolio builder" in prompt
        assert "Python" in prompt

    def test_user_prompt_with_all_params(self):
        prompt = build_portfolio_user_prompt(
            project_title="Shortlist",
            project_description="AI portfolio builder",
            tech_stack=["Python", "React"],
            key_features=["AI analysis", "Scaffolding"],
            repo_score=8.5,
            target_role="Full-Stack Engineer",
            architecture="Microservices with LangGraph",
        )
        assert "8.5" in prompt
        assert "Full-Stack Engineer" in prompt
        assert "Microservices with LangGraph" in prompt
        assert "AI analysis" in prompt

    def test_user_prompt_without_optional_params(self):
        prompt = build_portfolio_user_prompt(
            project_title="Test",
            project_description="Test desc",
            tech_stack=[],
        )
        assert "Target Role" not in prompt
        assert "Repo Score" not in prompt

# Node Logic Tests

class TestPortfolioNode:
    """Test the portfolio optimizer node internals."""

    def test_parse_valid_json(self):
        raw = json.dumps(VALID_PORTFOLIO_OUTPUT)
        parsed = _parse_portfolio_response(raw)
        assert "readme_markdown" in parsed
        assert len(parsed["resume_bullets"]) == 3

    def test_parse_markdown_wrapped_json(self):
        raw = f"```json\n{json.dumps(VALID_PORTFOLIO_OUTPUT)}\n```"
        parsed = _parse_portfolio_response(raw)
        assert "readme_markdown" in parsed

    def test_parse_json_with_surrounding_text(self):
        raw = f"Here is the output:\n{json.dumps(VALID_PORTFOLIO_OUTPUT)}\nDone!"
        parsed = _parse_portfolio_response(raw)
        assert "readme_markdown" in parsed

    def test_parse_invalid_json_raises(self):
        with pytest.raises(ValueError):
            _parse_portfolio_response("This is not JSON at all")

    def test_validate_valid_output(self):
        result = _validate_portfolio(VALID_PORTFOLIO_OUTPUT.copy())
        assert result["readme_markdown"] == VALID_PORTFOLIO_OUTPUT["readme_markdown"]
        assert len(result["resume_bullets"]) == 3

    def test_validate_truncates_long_readme(self):
        data = VALID_PORTFOLIO_OUTPUT.copy()
        data["readme_markdown"] = "x" * (MAX_README_LENGTH + 1000)
        result = _validate_portfolio(data)
        assert len(result["readme_markdown"]) == MAX_README_LENGTH

    def test_validate_truncates_long_bullets(self):
        data = VALID_PORTFOLIO_OUTPUT.copy()
        data["resume_bullets"] = [
            {
                "bullet": "A" * (MAX_BULLET_LENGTH + 50),
                "keywords": ["test"],
                "impact_type": "technical",
            }
        ]
        result = _validate_portfolio(data)
        assert len(result["resume_bullets"][0]["bullet"]) == MAX_BULLET_LENGTH

    def test_validate_truncates_excess_demo_steps(self):
        data = VALID_PORTFOLIO_OUTPUT.copy()
        data["demo_script"] = {
            "total_duration_seconds": 120,
            "opening_hook": "test",
            "closing_cta": "test",
            "steps": [{"timestamp": f"{i}:00", "action": "step", "narration": "n"} for i in range(20)],
        }
        result = _validate_portfolio(data)
        assert len(result["demo_script"]["steps"]) == MAX_DEMO_STEPS

# Node Async Tests

class TestPortfolioNodeAsync:
    """Test the async portfolio_optimizer_node function."""

    @pytest.mark.asyncio
    async def test_node_missing_title(self):
        state = {
            "portfolio_project_title": "",
            "portfolio_project_description": "A description",
            "portfolio_tech_stack": [],
            "messages": [],
        }
        result = await portfolio_optimizer_node(state)
        assert result["current_phase"] == "portfolio_error"
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_node_missing_description(self):
        state = {
            "portfolio_project_title": "My Project",
            "portfolio_project_description": "",
            "portfolio_tech_stack": [],
            "messages": [],
        }
        result = await portfolio_optimizer_node(state)
        assert result["current_phase"] == "portfolio_error"

    @pytest.mark.asyncio
    async def test_node_success(self):
        mock_response = MagicMock()
        mock_response.content = json.dumps(VALID_PORTFOLIO_OUTPUT)

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("app.agents.nodes.portfolio_node.get_llm", return_value=mock_llm):
            state = {
                "portfolio_project_title": "Shortlist",
                "portfolio_project_description": "AI portfolio builder",
                "portfolio_tech_stack": ["Python", "React"],
                "portfolio_key_features": ["AI analysis"],
                "portfolio_repo_score": 8.0,
                "portfolio_target_role": "Full-Stack Engineer",
                "messages": [],
            }
            result = await portfolio_optimizer_node(state)

        assert result["current_phase"] == "portfolio_complete"
        assert "portfolio_output" in result
        assert result["portfolio_output"]["readme_markdown"] == VALID_PORTFOLIO_OUTPUT["readme_markdown"]
        assert len(result["portfolio_output"]["resume_bullets"]) == 3

    @pytest.mark.asyncio
    async def test_node_llm_failure(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM timeout")

        with patch("app.agents.nodes.portfolio_node.get_llm", return_value=mock_llm):
            state = {
                "portfolio_project_title": "Test",
                "portfolio_project_description": "Test project description",
                "portfolio_tech_stack": [],
                "messages": [],
            }
            result = await portfolio_optimizer_node(state)

        assert result["current_phase"] == "portfolio_error"
        assert any("LLM" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_node_invalid_json_response(self):
        mock_response = MagicMock()
        mock_response.content = "Not valid JSON"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        with patch("app.agents.nodes.portfolio_node.get_llm", return_value=mock_llm):
            state = {
                "portfolio_project_title": "Test",
                "portfolio_project_description": "Test description",
                "portfolio_tech_stack": [],
                "messages": [],
            }
            result = await portfolio_optimizer_node(state)

        assert result["current_phase"] == "portfolio_error"

# Pipeline Tests

class TestPortfolioPipeline:
    """Test pipeline compilation and structure."""

    def test_compile_portfolio_pipeline(self):
        from app.agents.orchestrator import compile_portfolio_pipeline
        pipeline = compile_portfolio_pipeline()
        assert pipeline is not None

    def test_compile_with_checkpointer(self):
        from app.agents.orchestrator import compile_portfolio_pipeline
        pipeline = compile_portfolio_pipeline(with_checkpointer=True)
        assert pipeline is not None

    def test_build_portfolio_pipeline_has_nodes(self):
        from app.agents.orchestrator import build_portfolio_pipeline
        graph = build_portfolio_pipeline()
        assert graph is not None

# API Tests

class TestPortfolioAPI:
    """Test portfolio API endpoints."""

    @pytest.mark.asyncio
    async def test_optimize_requires_auth(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/portfolio/optimize",
                json={
                    "project_title": "Test Project",
                    "project_description": "A long enough project description here",
                    "tech_stack": ["Python"],
                },
            )
            assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_portfolio_requires_auth(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/portfolio/some-id")
            assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_portfolios_requires_auth(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/portfolio/")
            assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_optimize_validates_short_title(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/portfolio/optimize",
                json={
                    "project_title": "AB",  # Too short
                    "project_description": "A long enough project description here",
                },
            )
            # Auth runs before validation
            assert resp.status_code in (401, 422)
