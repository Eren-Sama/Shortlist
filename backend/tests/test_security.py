"""
Shortlist — Security Module Tests

Tests for security middleware and utility functions.
"""

import pytest

from app.security import sanitize_string, validate_github_url


class TestSanitizeString:
    """Tests for input sanitization."""

    def test_collapses_whitespace(self):
        result = sanitize_string("hello    world\n\tthere")
        assert result == "hello world there"

    def test_removes_null_bytes(self):
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_strips_leading_trailing_whitespace(self):
        result = sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_handles_empty_string(self):
        result = sanitize_string("")
        assert result == ""

    def test_preserves_normal_text(self):
        text = "Looking for a Senior Python Engineer with 5+ years"
        result = sanitize_string(text)
        assert result == text


class TestValidateGithubUrl:
    """Tests for GitHub URL validation and SSRF prevention."""

    def test_valid_https_github_url(self):
        result = validate_github_url("https://github.com/user/repo")
        assert result == "https://github.com/user/repo"

    def test_valid_deep_path(self):
        result = validate_github_url("https://github.com/org/repo")
        assert result == "https://github.com/org/repo"

    def test_rejects_http_url(self):
        with pytest.raises(ValueError):
            validate_github_url("http://github.com/user/repo")

    def test_rejects_non_github_host(self):
        with pytest.raises(ValueError):
            validate_github_url("https://gitlab.com/user/repo")

    def test_rejects_github_lookalike(self):
        with pytest.raises(ValueError):
            validate_github_url("https://github.com.evil.com/user/repo")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError):
            validate_github_url("https://github.com/../etc/passwd")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            validate_github_url("")

    def test_rejects_javascript_protocol(self):
        with pytest.raises(ValueError):
            validate_github_url("javascript:alert(1)")
