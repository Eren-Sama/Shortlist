"""
Shortlist — Scaffold Generator Tests

Tests for scaffold generation: prompts, node, pipeline, API, schemas.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Schema Tests

class TestScaffoldSchemas:
    """Test Pydantic schema validation for scaffold models."""

    def test_scaffold_request_valid(self):
        from app.schemas.scaffold import ScaffoldRequest

        req = ScaffoldRequest(
            project_title="My Test Project",
            project_description="A test project with enough description text.",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            include_docker=True,
            include_ci=True,
            include_tests=True,
        )
        assert req.project_title == "My Test Project"
        assert len(req.tech_stack) == 3
        assert req.include_docker is True

    def test_scaffold_request_with_project_id(self):
        from app.schemas.scaffold import ScaffoldRequest

        req = ScaffoldRequest(
            project_title="Linked Project",
            project_description="A scaffold linked to a capstone project.",
            tech_stack=["React", "Node.js"],
            project_id="abc-123",
            analysis_id="def-456",
        )
        assert req.project_id == "abc-123"
        assert req.analysis_id == "def-456"

    def test_scaffold_request_title_too_short(self):
        from app.schemas.scaffold import ScaffoldRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScaffoldRequest(
                project_title="AB",  # too short
                project_description="A valid long description for testing.",
            )

    def test_scaffold_request_description_too_short(self):
        from app.schemas.scaffold import ScaffoldRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScaffoldRequest(
                project_title="Valid Title",
                project_description="Too short",
            )

    def test_generated_file_model(self):
        from app.schemas.scaffold import GeneratedFile

        f = GeneratedFile(
            path="src/main.py",
            content="print('hello')",
            language="python",
            description="Entry point",
        )
        assert f.path == "src/main.py"
        assert f.language == "python"

    def test_scaffold_response_model(self):
        from app.schemas.scaffold import ScaffoldResponse, GeneratedFile

        resp = ScaffoldResponse(
            project_name="test-project",
            files=[
                GeneratedFile(
                    path="README.md",
                    content="# Test",
                    language="markdown",
                    description="Readme",
                ),
            ],
            file_tree="├── README.md",
        )
        assert resp.project_name == "test-project"
        assert len(resp.files) == 1

# Prompt Tests

class TestScaffoldPrompts:
    """Test scaffold prompt generation."""

    def test_system_prompt_exists(self):
        from app.prompts.scaffold_gen import SCAFFOLD_SYSTEM_PROMPT
        assert "production-ready" in SCAFFOLD_SYSTEM_PROMPT.lower()
        assert "JSON" in SCAFFOLD_SYSTEM_PROMPT

    def test_build_user_prompt_basic(self):
        from app.prompts.scaffold_gen import build_scaffold_user_prompt

        prompt = build_scaffold_user_prompt(
            project_title="Task Manager API",
            project_description="A RESTful task management API",
            tech_stack=["Python", "FastAPI"],
        )
        assert "Task Manager API" in prompt
        assert "FastAPI" in prompt
        assert "Include Docker: True" in prompt

    def test_build_user_prompt_with_options(self):
        from app.prompts.scaffold_gen import build_scaffold_user_prompt

        prompt = build_scaffold_user_prompt(
            project_title="CLI Tool",
            project_description="A command-line utility for data processing",
            tech_stack=["Go"],
            include_docker=False,
            include_ci=False,
            include_tests=True,
            complexity_level=2,
        )
        assert "Include Docker: False" in prompt
        assert "Include CI/CD: False" in prompt
        assert "Intermediate" in prompt

    def test_build_user_prompt_with_context(self):
        from app.prompts.scaffold_gen import build_scaffold_user_prompt

        prompt = build_scaffold_user_prompt(
            project_title="ML Pipeline",
            project_description="An ML training pipeline service",
            tech_stack=["Python", "PyTorch"],
            architecture="Microservice with queue-based processing",
            key_features=["Model versioning", "A/B testing"],
            recruiter_context="Demonstrates ML engineering skills",
        )
        assert "Microservice" in prompt
        assert "Model versioning" in prompt
        assert "Demonstrates ML" in prompt

# Scaffold Node Tests

class TestScaffoldNode:
    """Test the scaffold_generator_node."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response with valid scaffold JSON."""
        scaffold_json = json.dumps({
            "project_name": "task-manager-api",
            "files": [
                {
                    "path": "src/main.py",
                    "content": "from fastapi import FastAPI\napp = FastAPI()\n",
                    "language": "python",
                    "description": "Application entry point",
                },
                {
                    "path": "README.md",
                    "content": "# Task Manager API\n\nA RESTful task management API.",
                    "language": "markdown",
                    "description": "Project readme",
                },
                {
                    "path": "requirements.txt",
                    "content": "fastapi>=0.100.0\nuvicorn>=0.23.0\n",
                    "language": "text",
                    "description": "Python dependencies",
                },
            ],
            "file_tree": "├── src/\n│   └── main.py\n├── README.md\n└── requirements.txt",
        })
        mock_resp = MagicMock()
        mock_resp.content = scaffold_json
        return mock_resp

    @pytest.mark.asyncio
    async def test_scaffold_node_success(self, mock_llm_response):
        from app.agents.nodes.scaffold_node import scaffold_generator_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        state = {
            "scaffold_project_title": "Task Manager API",
            "scaffold_project_description": "A RESTful task management API",
            "scaffold_tech_stack": ["Python", "FastAPI"],
            "scaffold_options": {"include_docker": True, "include_ci": True, "include_tests": True},
            "generated_projects": [],
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.scaffold_node.get_llm", return_value=mock_llm):
            result = await scaffold_generator_node(state)

        assert result["current_phase"] == "scaffold_generation_complete"
        assert len(result["scaffold_files"]) == 3
        assert result["scaffold_project_name"] == "task-manager-api"
        assert "main.py" in result["scaffold_file_tree"]

    @pytest.mark.asyncio
    async def test_scaffold_node_with_capstone_context(self, mock_llm_response):
        from app.agents.nodes.scaffold_node import scaffold_generator_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

        state = {
            "scaffold_project_title": "Task Manager API",
            "scaffold_project_description": "A RESTful task management API",
            "scaffold_tech_stack": ["Python", "FastAPI"],
            "scaffold_options": {},
            "generated_projects": [
                {
                    "title": "Task Manager API",
                    "architecture": {"description": "Microservice with worker queues"},
                    "key_features": ["Real-time updates", "Task dependencies"],
                    "complexity_level": 3,
                    "recruiter_match_reasoning": "Shows distributed systems skills",
                }
            ],
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.scaffold_node.get_llm", return_value=mock_llm):
            result = await scaffold_generator_node(state)

        assert result["current_phase"] == "scaffold_generation_complete"
        assert len(result["scaffold_files"]) >= 1

    @pytest.mark.asyncio
    async def test_scaffold_node_invalid_json(self):
        from app.agents.nodes.scaffold_node import scaffold_generator_node

        mock_resp = MagicMock()
        mock_resp.content = "This is not valid JSON at all"
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

        state = {
            "scaffold_project_title": "Test",
            "scaffold_project_description": "Test description",
            "scaffold_tech_stack": [],
            "scaffold_options": {},
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.scaffold_node.get_llm", return_value=mock_llm):
            result = await scaffold_generator_node(state)

        assert "scaffold_generation_failed" in result["current_phase"]
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_scaffold_node_llm_exception(self):
        from app.agents.nodes.scaffold_node import scaffold_generator_node

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("LLM offline"))

        state = {
            "scaffold_project_title": "Test",
            "scaffold_project_description": "Test",
            "scaffold_tech_stack": [],
            "scaffold_options": {},
            "messages": [],
            "errors": [],
        }

        with patch("app.agents.nodes.scaffold_node.get_llm", return_value=mock_llm):
            result = await scaffold_generator_node(state)

        assert "scaffold_generation_failed" in result["current_phase"]
        assert len(result["errors"]) > 0

# Scaffold Validation / Security Tests

class TestScaffoldValidation:
    """Test path sanitization and content validation."""

    def test_sanitize_path_valid(self):
        from app.agents.nodes.scaffold_node import _sanitize_path
        assert _sanitize_path("src/main.py") == "src/main.py"
        assert _sanitize_path("README.md") == "README.md"
        assert _sanitize_path(".gitignore") == ".gitignore"

    def test_sanitize_path_traversal_blocked(self):
        from app.agents.nodes.scaffold_node import _sanitize_path
        assert _sanitize_path("../../etc/passwd") is None
        assert _sanitize_path("src/../../../secret") is None

    def test_sanitize_path_forbidden_dirs(self):
        from app.agents.nodes.scaffold_node import _sanitize_path
        assert _sanitize_path("node_modules/pkg/file.js") is None
        assert _sanitize_path("__pycache__/module.pyc") is None
        assert _sanitize_path(".git/config") is None

    def test_sanitize_path_empty_and_long(self):
        from app.agents.nodes.scaffold_node import _sanitize_path
        assert _sanitize_path("") is None
        assert _sanitize_path("a" * 400) is None

    def test_validate_scaffold_size_limit(self):
        from app.agents.nodes.scaffold_node import _validate_scaffold

        big_content = "x" * (600 * 1024)  # 600 KB
        scaffold = {
            "project_name": "test",
            "files": [
                {"path": "big.txt", "content": big_content, "language": "text"},
                {"path": "more.txt", "content": "should be truncated", "language": "text"},
            ],
            "file_tree": "test",
        }
        result = _validate_scaffold(scaffold)
        # The first file exceeding limit should cause truncation
        assert len(result["files"]) <= 1

    def test_validate_scaffold_project_name_sanitization(self):
        from app.agents.nodes.scaffold_node import _validate_scaffold

        scaffold = {
            "project_name": "My Project!! @#$",
            "files": [],
            "file_tree": "",
        }
        result = _validate_scaffold(scaffold)
        # Should only contain a-z, 0-9, hyphens
        assert result["project_name"] == "myproject"

    def test_parse_scaffold_response_markdown_wrapped(self):
        from app.agents.nodes.scaffold_node import _parse_scaffold_response

        wrapped = '```json\n{"project_name": "test", "files": [], "file_tree": ""}\n```'
        result = _parse_scaffold_response(wrapped)
        assert result["project_name"] == "test"

# Pipeline / Orchestrator Tests

class TestScaffoldPipeline:
    """Test scaffold pipeline compilation."""

    def test_compile_scaffold_pipeline(self):
        from app.agents.orchestrator import compile_scaffold_pipeline
        pipeline = compile_scaffold_pipeline()
        assert pipeline is not None

    def test_build_scaffold_pipeline_nodes(self):
        from app.agents.orchestrator import build_scaffold_pipeline
        graph = build_scaffold_pipeline()
        assert "scaffold_generator" in graph.nodes

# API Endpoint Tests

class TestScaffoldAPI:
    """Test scaffold API endpoints."""

    def test_scaffold_generate_requires_auth(self, client):
        response = client.post(
            "/api/v1/scaffold/generate",
            json={
                "project_title": "Test Project",
                "project_description": "A test project with enough text.",
                "tech_stack": ["Python"],
            },
        )
        assert response.status_code in (401, 403)

    def test_scaffold_list_requires_auth(self, client):
        response = client.get("/api/v1/scaffold/")
        assert response.status_code in (401, 403)

    def test_scaffold_get_requires_auth(self, client):
        response = client.get("/api/v1/scaffold/some-id")
        assert response.status_code in (401, 403)

    def test_scaffold_generate_validation(self, client):
        """Short title should fail validation (auth first, so 401 without token)."""
        response = client.post(
            "/api/v1/scaffold/generate",
            json={
                "project_title": "AB",
                "project_description": "desc",
            },
        )
        # Auth check happens before validation, so 401 without token
        assert response.status_code in (401, 422)
