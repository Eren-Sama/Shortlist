"""
Shortlist — Schema Validation Tests

Tests for Pydantic request/response models.
"""

import pytest
from pydantic import ValidationError

from app.schemas.jd import JDAnalysisRequest, CompanyType
from app.schemas.repo import RepoAnalysisRequest
from app.schemas.capstone import CapstoneGenerationRequest
from app.schemas.scaffold import ScaffoldRequest
from app.schemas.portfolio import PortfolioOptimizeRequest


class TestJDSchema:
    """Validation tests for JD analysis schemas."""

    def test_valid_jd_request(self):
        req = JDAnalysisRequest(
            jd_text="x" * 100,
            role="Backend Engineer",
            company_type=CompanyType.STARTUP,
        )
        assert req.role == "Backend Engineer"
        assert req.company_type == CompanyType.STARTUP

    def test_jd_text_too_short(self):
        with pytest.raises(ValidationError):
            JDAnalysisRequest(
                jd_text="short",
                role="Engineer",
                company_type=CompanyType.STARTUP,
            )

    def test_jd_text_too_long(self):
        with pytest.raises(ValidationError):
            JDAnalysisRequest(
                jd_text="x" * 20000,
                role="Engineer",
                company_type=CompanyType.STARTUP,
            )

    def test_invalid_company_type(self):
        with pytest.raises(ValidationError):
            JDAnalysisRequest(
                jd_text="x" * 100,
                role="Engineer",
                company_type="google",  # type: ignore
            )

    def test_all_company_types_valid(self):
        for ct in CompanyType:
            req = JDAnalysisRequest(
                jd_text="x" * 100,
                role="Engineer",
                company_type=ct,
            )
            assert req.company_type == ct

    def test_geography_optional(self):
        req = JDAnalysisRequest(
            jd_text="x" * 100,
            role="Engineer",
            company_type=CompanyType.FAANG,
        )
        assert req.geography is None


class TestRepoSchema:
    """Validation tests for repo analysis schemas."""

    def test_valid_github_url(self):
        req = RepoAnalysisRequest(
            github_url="https://github.com/user/repo"
        )
        assert "github.com" in req.github_url

    def test_rejects_non_github_url(self):
        with pytest.raises(ValidationError):
            RepoAnalysisRequest(
                github_url="https://gitlab.com/user/repo"
            )

    def test_rejects_malformed_url(self):
        with pytest.raises(ValidationError):
            RepoAnalysisRequest(
                github_url="not-a-url-at-all"
            )


class TestCapstoneSchema:
    """Validation tests for capstone schemas."""

    def test_valid_capstone_request(self):
        req = CapstoneGenerationRequest(analysis_id="abc-123")
        assert req.analysis_id == "abc-123"


class TestScaffoldSchema:
    """Validation tests for scaffold schemas."""

    def test_valid_scaffold_request(self):
        req = ScaffoldRequest(
            project_title="My API Gateway",
            project_description="A high-performance API gateway with rate limiting",
        )
        assert req.project_title == "My API Gateway"


class TestPortfolioSchema:
    """Validation tests for portfolio schemas."""

    def test_valid_portfolio_request(self):
        req = PortfolioOptimizeRequest(
            project_title="My Project",
            project_description="A cool project that does things",
        )
        assert req.project_title == "My Project"
