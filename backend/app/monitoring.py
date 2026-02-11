"""Monitoring endpoints: health checks, Prometheus metrics, and application info."""

import time
from collections import defaultdict
from typing import Optional

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("monitoring")

# Application Metrics — In-Memory Counters
class ApplicationMetrics:
    """
    Lightweight in-memory metrics collector.
    
    For production at scale, replace with Prometheus client
    (prometheus_client) or push to Datadog/CloudWatch.
    """

    def __init__(self):
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._status_codes: dict[int, int] = defaultdict(int)
        self._endpoint_latencies: dict[str, list[float]] = defaultdict(list)
        self._pipeline_runs: dict[str, int] = defaultdict(int)
        self._pipeline_errors: dict[str, int] = defaultdict(int)
        self._max_tracked_endpoints = 200  

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def record_request(self, status_code: int, path: str, latency_ms: float):
        """Record a completed HTTP request."""
        self._request_count += 1
        self._status_codes[status_code] += 1
        if status_code >= 500:
            self._error_count += 1
        if len(self._endpoint_latencies) >= self._max_tracked_endpoints and path not in self._endpoint_latencies:
            return

        latencies = self._endpoint_latencies[path]
        latencies.append(latency_ms)
        if len(latencies) > 1000:
            self._endpoint_latencies[path] = latencies[-500:]

    def record_pipeline_run(self, pipeline_name: str, success: bool):
        """Record a pipeline execution."""
        self._pipeline_runs[pipeline_name] += 1
        if not success:
            self._pipeline_errors[pipeline_name] += 1

    def snapshot(self) -> dict:
        """Return a point-in-time metrics snapshot."""
        endpoint_stats = {}
        for path, latencies in self._endpoint_latencies.items():
            if not latencies:
                continue
            sorted_lat = sorted(latencies)
            n = len(sorted_lat)
            endpoint_stats[path] = {
                "count": n,
                "p50_ms": sorted_lat[n // 2],
                "p95_ms": sorted_lat[int(n * 0.95)],
                "p99_ms": sorted_lat[int(n * 0.99)],
                "avg_ms": round(sum(sorted_lat) / n, 2),
            }

        return {
            "uptime_seconds": round(self.uptime_seconds, 1),
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": (
                round(self._error_count / self._request_count, 4)
                if self._request_count > 0 else 0.0
            ),
            "status_codes": dict(self._status_codes),
            "endpoint_latencies": endpoint_stats,
            "pipelines": {
                name: {
                    "runs": self._pipeline_runs[name],
                    "errors": self._pipeline_errors.get(name, 0),
                }
                for name in self._pipeline_runs
            },
        }

# Singleton metrics instance
_metrics: Optional[ApplicationMetrics] = None

def get_metrics() -> ApplicationMetrics:
    """Get or create the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = ApplicationMetrics()
    return _metrics

# Deep Health Check
async def check_database_health() -> dict:
    """
    Verify Supabase connectivity by performing a lightweight query.
    Returns status and latency.
    """
    from app.database import get_supabase

    try:
        db = get_supabase()
        start = time.time()
        # Simple existence check — minimal overhead
        result = await db.table("jd_analyses").select("id", count="exact").limit(1).execute()
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "connected": True,
        }
    except RuntimeError:
        return {
            "status": "unavailable",
            "latency_ms": None,
            "connected": False,
            "reason": "Client not initialized",
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "latency_ms": None,
            "connected": False,
            "reason": "Connection failed",
        }

async def check_llm_health() -> dict:
    """
    Verify LLM provider API key is configured.
    Does NOT make an actual LLM call (too expensive for health checks).
    """
    settings = get_settings()
    has_groq = bool(settings.GROQ_API_KEY)
    has_openai = bool(settings.OPENAI_API_KEY)

    return {
        "status": "healthy" if has_groq else "degraded",
        "providers": {
            "groq": "configured" if has_groq else "missing",
            "openai": "configured" if has_openai else "not_configured",
        },
    }

async def deep_health_check() -> dict:
    """
    Comprehensive health check for load balancers and monitoring.
    
    Returns:
        dict with overall status and component health
    """
    settings = get_settings()
    metrics = get_metrics()

    db_health = await check_database_health()
    llm_health = await check_llm_health()

    # Overall status: healthy only if all critical components are up
    components_healthy = (
        db_health["status"] in ("healthy", "unavailable")  # unavailable OK in dev
        and llm_health["status"] != "unhealthy"
    )

    return {
        "status": "healthy" if components_healthy else "unhealthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(metrics.uptime_seconds, 1),
        "components": {
            "database": db_health,
            "llm": llm_health,
        },
    }
