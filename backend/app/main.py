"""FastAPI application entry point with lifespan, security middleware, and versioned routing."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import init_supabase, close_supabase
from app.logging_config import setup_logging, get_logger
from app.monitoring import get_metrics, deep_health_check
from app.security import (
    configure_cors,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
)
from app.api.v1 import router as api_v1_router

logger = get_logger("main")

# Request-ID Tracing Middleware
class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique X-Request-ID to every request.
    Enables end-to-end tracing across frontend → backend → logs.

    - Respects incoming X-Request-ID from reverse proxy / gateway
    - Falls back to generating a new UUID4
    - Injects into response headers for client correlation
    - Records request metrics (latency, status code)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Inject tracing header
        response.headers["X-Request-ID"] = request_id

        # Record metrics (skip health/docs endpoints)
        path = request.url.path
        if path not in ("/health", "/health/deep", "/metrics", "/docs", "/openapi.json"):
            get_metrics().record_request(response.status_code, path, latency_ms)

        # Log slow requests (> 5 seconds)
        if latency_ms > 5000:
            logger.warning(
                f"Slow request: {request.method} {path} "
                f"took {latency_ms}ms [rid={request_id}]"
            )

        return response

# Application Lifespan — Startup / Shutdown
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manages application lifecycle:
    - Startup: init logging, connect DB, warm up services
    - Shutdown: close DB connections, cleanup resources
    """
    # ── Startup ──
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting Shortlist API",
        extra={"extra_data": {
            "environment": settings.ENVIRONMENT,
            "version": settings.APP_VERSION,
        }},
    )

    # Initialize Supabase (skip if credentials not set — allows local dev)
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        try:
            await init_supabase()
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            # Don't crash — allow app to start for local development
    else:
        logger.warning(
            "Supabase credentials not configured. "
            "Database features will be unavailable."
        )

    yield

    # ── Shutdown ──
    await close_supabase()
    logger.info("Shortlist API shut down cleanly")

# Application Factory
def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Recruiter-Aware Portfolio Architect",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )

    # ── Middleware Stack (order matters — outermost first) ──
    # 1. Request size limit (reject before processing)
    app.add_middleware(RequestSizeLimitMiddleware)
    # 2. Rate limiting
    app.add_middleware(RateLimitMiddleware)
    # 3. Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    # 4. Request-ID tracing + metrics collection
    app.add_middleware(RequestTracingMiddleware)
    # 5. CORS (must be last middleware added = first to run)
    configure_cors(app)

    # ── Exception Handlers ──
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Custom validation error response.
        Strips internal details — returns clean error messages only.
        """
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " → ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all exception handler.
        Logs the full error internally, returns safe message to client.
        NEVER leak stack traces or internal details to the client.
        """
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again later."},
        )

    # ── Routes ──
    @app.get("/")
    async def root():
        return {"status": "ok"}

    @app.get("/health", tags=["system"])
    async def health_check():
        """Lightweight health check for load balancers."""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/health/deep", tags=["system"])
    async def deep_health():
        """
        Deep health check — verifies DB connectivity, LLM config, etc.
        Use this for comprehensive monitoring; NOT for high-frequency LB pings.
        """
        result = await deep_health_check()
        status_code = 200 if result["status"] == "healthy" else 503
        return JSONResponse(content=result, status_code=status_code)

    @app.get("/metrics", tags=["system"])
    async def metrics_endpoint(request: Request):
        """
        Application metrics snapshot.
        Returns request counts, latencies (p50/p95/p99), error rates,
        and pipeline execution stats.

        Protected: only accessible in development or from localhost.
        """
        if settings.ENVIRONMENT == "production":
            client_ip = request.client.host if request.client else ""
            if client_ip not in ("127.0.0.1", "::1", "localhost"):
                return JSONResponse(
                    content={"detail": "Not available"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        return get_metrics().snapshot()

    # Mount versioned API router
    app.include_router(api_v1_router, prefix="/api/v1")

    return app

# Create the application instance
app = create_app()
