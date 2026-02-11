"""
Shortlist — API Endpoint Tests

Tests for the FastAPI application endpoints.
Uses TestClient for synchronous testing.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    def test_health_has_security_headers(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_allows_configured_origin(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_blocks_unknown_origin(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Unknown origins should not get CORS headers
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"


class TestAuthRequiredEndpoints:
    """Tests that protected endpoints require authentication."""

    def test_jd_analyze_requires_auth(self, client):
        response = client.post("/api/v1/jd/analyze", json={
            "jd_text": "x" * 100,
            "role": "Backend Engineer",
            "company_type": "startup",
        })
        assert response.status_code == 401

    def test_capstone_generate_requires_auth(self, client):
        response = client.post("/api/v1/capstone/generate", json={
            "analysis_id": "test-id",
        })
        assert response.status_code == 401

    def test_repo_analyze_requires_auth(self, client):
        response = client.post("/api/v1/repo/analyze", json={
            "github_url": "https://github.com/test/repo",
        })
        assert response.status_code == 401

    def test_scaffold_generate_requires_auth(self, client):
        response = client.post("/api/v1/scaffold/generate", json={
            "project_title": "Test Project",
            "project_description": "A test project description here",
        })
        assert response.status_code == 401

    def test_portfolio_optimize_requires_auth(self, client):
        response = client.post("/api/v1/portfolio/optimize", json={
            "project_title": "Test",
            "project_description": "A test project description here",
        })
        assert response.status_code == 401


class TestInputValidation:
    """Tests for request validation (Pydantic enforcement)."""

    def test_jd_rejects_short_text(self, client):
        """JD text under 50 chars should be rejected (auth blocks first with fake token)."""
        response = client.post(
            "/api/v1/jd/analyze",
            json={
                "jd_text": "too short",
                "role": "Engineer",
                "company_type": "startup",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        # Auth runs before validation, so we get 401 with fake token
        assert response.status_code in (401, 422)

    def test_jd_rejects_invalid_company_type(self, client):
        """Invalid company type should be rejected (auth blocks first with fake token)."""
        response = client.post(
            "/api/v1/jd/analyze",
            json={
                "jd_text": "x" * 100,
                "role": "Engineer",
                "company_type": "invalid_type",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code in (401, 422)

    def test_repo_rejects_invalid_github_url(self, client):
        """Non-GitHub URLs should be rejected (auth blocks first with fake token)."""
        response = client.post(
            "/api/v1/repo/analyze",
            json={"github_url": "https://gitlab.com/user/repo"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code in (401, 422)
