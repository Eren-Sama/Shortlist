"""Security middleware: CORS, rate limiting, security headers, and input sanitization."""

import time
import hashlib
import re
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

# CORS — Strict Origin Enforcement
def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS with explicit allowed origins.
    Never use allow_origins=["*"] in production.
    """
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-Idempotency-Key",
        ],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
        max_age=600,  # Cache preflight for 10 minutes
    )

# Security Headers — OWASP Recommendations
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security headers into every response.
    Prevents XSS, clickjacking, MIME sniffing, etc.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Strict-Transport-Security only in production
        settings = get_settings()
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Remove server identification headers
        if "server" in response.headers:
            del response.headers["server"]

        return response

# Rate Limiter — Sliding Window Counter
class RateLimiter:
    """
    In-memory sliding window rate limiter.
    Keyed by client IP (hashed for privacy).

    For production at scale, replace with Redis-backed limiter.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_global_cleanup: float = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Hash the client IP for privacy-safe rate tracking."""
        client_ip = request.client.host if request.client else "unknown"
        return hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    def _cleanup(self, key: str, now: float) -> None:
        """Remove expired timestamps from the window."""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]
        # Periodic global cleanup: evict stale keys every 5 minutes
        # to prevent unbounded memory growth from unique IPs
        if now - self._last_global_cleanup > 300:
            stale_keys = [
                k for k, timestamps in self._requests.items()
                if not timestamps or timestamps[-1] < cutoff
            ]
            for k in stale_keys:
                del self._requests[k]
            self._last_global_cleanup = now

    def check(self, request: Request) -> tuple[bool, int]:
        """
        Returns (allowed: bool, remaining: int).
        """
        now = time.time()
        key = self._get_client_key(request)
        self._cleanup(key, now)

        current_count = len(self._requests[key])
        remaining = max(0, self.max_requests - current_count)

        if current_count >= self.max_requests:
            return False, 0

        self._requests[key].append(now)
        return True, remaining - 1

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Applies rate limiting to all non-health-check endpoints.
    Returns 429 with Retry-After header when limit is exceeded.
    """

    def __init__(self, app: FastAPI, **kwargs):
        super().__init__(app, **kwargs)
        settings = get_settings()
        self.limiter = RateLimiter(
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Always allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip rate limiting for health checks and docs
        skip_paths = {"/health", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in skip_paths:
            return await call_next(request)

        allowed, remaining = self.limiter.check(request)

        if not allowed:
            return Response(
                content='{"detail": "Rate limit exceeded. Please retry later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

# Request Size Limiter
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests exceeding the configured size limit.
    Prevents memory exhaustion from oversized payloads.
    Checks both Content-Length header AND actual body size
    to prevent bypasses via chunked transfer encoding.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Always allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        settings = get_settings()
        max_bytes = settings.MAX_REQUEST_SIZE_MB * 1024 * 1024

        # Fast-reject via Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Maximum: {settings.MAX_REQUEST_SIZE_MB}MB",
            )

        # For requests without Content-Length (chunked), read and check body
        if request.method in ("POST", "PUT", "PATCH") and not content_length:
            body = await request.body()
            if len(body) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request body too large. Maximum: {settings.MAX_REQUEST_SIZE_MB}MB",
                )

        return await call_next(request)

# Input Sanitization Utilities
def sanitize_string(value: str, max_length: int = 10_000) -> str:
    """
    Sanitize user input:
    - Strip leading/trailing whitespace
    - Truncate to max_length
    - Remove null bytes
    - Normalize whitespace
    """
    if not value:
        return ""
    value = value.strip()[:max_length]
    value = value.replace("\x00", "")
    value = re.sub(r"\s+", " ", value)  # Collapse multiple whitespace
    return value

def validate_github_url(url: str) -> str:
    """
    Validate and normalize a GitHub repository URL.
    Only allows github.com HTTPS URLs to prevent SSRF.
    """
    url = sanitize_string(url, max_length=500).strip().rstrip("/")

    # Strict pattern: only github.com repos
    pattern = r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+/?$"
    if not re.match(pattern, url):
        raise ValueError(
            "Invalid GitHub URL. Must be: https://github.com/{owner}/{repo}"
        )

    return url
