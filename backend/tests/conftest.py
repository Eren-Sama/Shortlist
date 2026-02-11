"""
Shortlist — Shared Test Fixtures

Provides reusable fixtures for the test suite.
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# ----- Environment setup (before any app imports) -----
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production-1234567890")
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-tests-only")
os.environ.setdefault("GROQ_API_KEY", "gsk_test_key_for_testing_only")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mocked Supabase async client."""
    mock = AsyncMock()
    mock.table = MagicMock()
    mock.table.return_value.insert = MagicMock(return_value=AsyncMock())
    mock.table.return_value.select = MagicMock(return_value=AsyncMock())
    return mock


@pytest.fixture
def auth_headers():
    """
    Returns headers with a fake JWT that will fail real verification
    but is useful for testing validation logic before auth kicks in.
    """
    return {"Authorization": "Bearer fake-jwt-for-testing"}


@pytest.fixture
def sample_jd_text():
    """A realistic JD text for testing."""
    return (
        "We are looking for a Senior Backend Engineer with 5+ years of experience "
        "in Python, FastAPI, and distributed systems. You will design and build "
        "microservices that handle millions of requests per day. Experience with "
        "PostgreSQL, Redis, Docker, and Kubernetes is required. Bonus: experience "
        "with machine learning pipelines and real-time data processing. Strong "
        "understanding of REST API design, authentication, and authorization patterns."
    )


@pytest.fixture
def sample_skill_profile():
    """A sample parsed skill profile."""
    return {
        "primary_skills": [
            {"name": "Python", "category": "language", "weight": 9, "source": "explicit"},
            {"name": "FastAPI", "category": "framework", "weight": 8, "source": "explicit"},
            {"name": "PostgreSQL", "category": "database", "weight": 7, "source": "explicit"},
        ],
        "secondary_skills": [
            {"name": "Redis", "category": "database", "weight": 5, "source": "explicit"},
            {"name": "Docker", "category": "devops", "weight": 5, "source": "explicit"},
        ],
        "inferred_skills": [
            {"name": "Linux", "category": "devops", "weight": 3, "source": "inferred"},
        ],
        "experience_level": "senior",
        "domain_keywords": ["microservices", "distributed systems", "real-time"],
    }
