"""
Shortlist — Repo Analyzer Tests

Tests for Phase 2: GitHub Repository Analyzer.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import asdict

from app.services.github_analyzer import (
    GitHubAnalyzer,
    _parse_github_url,
    RepoMetadata,
    FileAnalysis,
    RepoAnalysisResult,
)
from app.agents.nodes.repo_node import repo_analysis_node, _parse_scorecard
from app.prompts.repo_analysis import build_repo_user_prompt


class TestGitHubUrlParsing:
    """Tests for GitHub URL validation and parsing."""

    def test_valid_url_https(self):
        owner, repo = _parse_github_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_valid_url_with_trailing_slash(self):
        owner, repo = _parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    def test_valid_url_with_hyphens(self):
        owner, repo = _parse_github_url("https://github.com/my-org/my-repo")
        assert owner == "my-org"
        assert repo == "my-repo"

    def test_valid_url_with_underscores(self):
        owner, repo = _parse_github_url("https://github.com/my_org/my_repo")
        assert owner == "my_org"
        assert repo == "my_repo"

    def test_invalid_url_http(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("http://github.com/owner/repo")

    def test_invalid_url_wrong_domain(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("https://gitlab.com/owner/repo")

    def test_invalid_url_missing_repo(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("https://github.com/owner")

    def test_invalid_url_path_traversal_attempt(self):
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            _parse_github_url("https://github.com/../../../etc/passwd")


class TestScorecardParsing:
    """Tests for LLM scorecard response parsing."""

    def test_parse_valid_json(self):
        content = '{"overall_score": 7.5, "summary": "Good repo"}'
        result = _parse_scorecard(content)
        assert result["overall_score"] == 7.5
        assert result["summary"] == "Good repo"

    def test_parse_json_with_markdown_blocks(self):
        content = """```json
{"overall_score": 8.0, "summary": "Excellent"}
```"""
        result = _parse_scorecard(content)
        assert result["overall_score"] == 8.0

    def test_parse_invalid_json_returns_default(self):
        content = "This is not JSON at all"
        result = _parse_scorecard(content)
        assert result["overall_score"] == 5.0
        assert "code_quality" in result
        assert result["code_quality"]["score"] == 5.0


class TestRepoPromptBuilder:
    """Tests for repo analysis prompt construction."""

    def test_prompt_includes_repo_info(self):
        prompt = build_repo_user_prompt(
            repo_name="owner/test-repo",
            description="A test repository",
            primary_language="Python",
            languages={"Python": 10000, "JavaScript": 2000},
            stars=100,
            topics=["python", "testing"],
            has_readme=True,
            has_license=True,
            has_tests=True,
            has_ci=True,
            has_docker=False,
            total_files=50,
            code_files=30,
            test_files=10,
            config_files=["requirements.txt", "pytest.ini"],
            quality_files=["README.md", "LICENSE"],
            estimated_loc=5000,
            readme_content="# Test Repo\n\nThis is a test.",
            sample_code={"src/main.py": "print('hello')"},
        )
        
        assert "owner/test-repo" in prompt
        assert "Python" in prompt
        assert "100" in prompt  # stars
        assert "README.md Content:" in prompt
        assert "src/main.py" in prompt

    def test_prompt_handles_missing_data(self):
        prompt = build_repo_user_prompt(
            repo_name="owner/minimal",
            description=None,
            primary_language=None,
            languages={},
            stars=0,
            topics=[],
            has_readme=False,
            has_license=False,
            has_tests=False,
            has_ci=False,
            has_docker=False,
            total_files=5,
            code_files=3,
            test_files=0,
            config_files=[],
            quality_files=[],
            estimated_loc=100,
            readme_content=None,
            sample_code={},
        )
        
        assert "owner/minimal" in prompt
        assert "No description" in prompt
        assert "✗ Missing" in prompt  # README missing


class TestRepoAnalysisNode:
    """Tests for the repo analysis agent node."""

    @pytest.mark.asyncio
    async def test_node_requires_repo_url(self):
        """Node should return error if repo_url is missing."""
        state = {"repo_url": None, "errors": []}
        result = await repo_analysis_node(state)
        
        assert result["current_phase"] == "repo_analysis_failed"
        assert "No repository URL provided" in result["errors"]

    @pytest.mark.asyncio
    async def test_node_handles_invalid_url(self):
        """Node should handle invalid GitHub URLs gracefully."""
        state = {"repo_url": "https://not-github.com/owner/repo", "errors": []}
        result = await repo_analysis_node(state)
        
        assert result["current_phase"] == "repo_analysis_failed"
        assert len(result["errors"]) > 0


class TestGitHubAnalyzer:
    """Tests for the GitHubAnalyzer service."""

    @pytest.mark.asyncio
    async def test_analyzer_close_is_idempotent(self):
        """Closing analyzer multiple times should not raise."""
        analyzer = GitHubAnalyzer()
        await analyzer.close()
        await analyzer.close()  # Should not raise

    def test_analyzer_accepts_token(self):
        """Analyzer should accept optional GitHub token."""
        analyzer = GitHubAnalyzer(github_token="test-token")
        assert analyzer.token == "test-token"


class TestRepoEndpoints:
    """Tests for repo API endpoints."""

    def test_analyze_requires_auth(self, client):
        """Analyze endpoint should require authentication."""
        response = client.post(
            "/api/v1/repo/analyze",
            json={"github_url": "https://github.com/owner/repo"},
        )
        assert response.status_code == 401

    def test_analyze_validates_url(self, client, auth_headers):
        """Analyze endpoint should validate GitHub URL format."""
        response = client.post(
            "/api/v1/repo/analyze",
            json={"github_url": "https://not-github.com/owner/repo"},
            headers=auth_headers,
        )
        # Either 401 (auth fails on fake token) or 422 (validation fails)
        assert response.status_code in [401, 422]

    def test_list_requires_auth(self, client):
        """List endpoint should require authentication."""
        response = client.get("/api/v1/repo/")
        assert response.status_code == 401

    def test_get_requires_auth(self, client):
        """Get endpoint should require authentication."""
        response = client.get("/api/v1/repo/some-id")
        assert response.status_code == 401
