"""
Shortlist — Phase 5 Tests: Production Deploy & Monitoring

Tests for:
- Monitoring module (metrics, health checks)
- Request-ID tracing
- Production config validation
- New API endpoints (/health/deep, /metrics)
"""

import time
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Monitoring Module Tests

class TestApplicationMetrics:
    """Tests for the in-memory metrics collector."""

    def test_initial_state(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        snap = m.snapshot()
        assert snap["total_requests"] == 0
        assert snap["total_errors"] == 0
        assert snap["error_rate"] == 0.0
        assert snap["status_codes"] == {}
        assert snap["endpoint_latencies"] == {}
        assert snap["pipelines"] == {}
        assert snap["uptime_seconds"] >= 0.0

    def test_record_request(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        m.record_request(200, "/api/v1/jd/analyze", 150.5)
        m.record_request(200, "/api/v1/jd/analyze", 200.3)
        m.record_request(404, "/api/v1/jd/missing", 10.0)
        snap = m.snapshot()
        assert snap["total_requests"] == 3
        assert snap["total_errors"] == 0
        assert snap["status_codes"] == {200: 2, 404: 1}
        assert "/api/v1/jd/analyze" in snap["endpoint_latencies"]

    def test_record_server_error_increments_error_count(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        m.record_request(500, "/api/v1/repo/analyze", 1000.0)
        m.record_request(503, "/health/deep", 50.0)
        m.record_request(200, "/api/v1/jd/analyze", 100.0)
        snap = m.snapshot()
        assert snap["total_errors"] == 2
        assert snap["error_rate"] == pytest.approx(2 / 3, abs=0.01)

    def test_record_pipeline_run(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        m.record_pipeline_run("jd", True)
        m.record_pipeline_run("jd", True)
        m.record_pipeline_run("jd", False)
        m.record_pipeline_run("repo", True)
        snap = m.snapshot()
        assert snap["pipelines"]["jd"]["runs"] == 3
        assert snap["pipelines"]["jd"]["errors"] == 1
        assert snap["pipelines"]["repo"]["runs"] == 1
        assert snap["pipelines"]["repo"]["errors"] == 0

    def test_latency_percentiles(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        # Add 100 requests with known latencies
        for i in range(1, 101):
            m.record_request(200, "/api/v1/test", float(i))
        snap = m.snapshot()
        stats = snap["endpoint_latencies"]["/api/v1/test"]
        assert stats["count"] == 100
        assert stats["p50_ms"] == pytest.approx(50.0, abs=1.0)
        assert stats["p95_ms"] == pytest.approx(95.0, abs=1.0)
        assert stats["p99_ms"] == pytest.approx(99.0, abs=1.0)
        assert stats["avg_ms"] == pytest.approx(50.5, abs=0.1)

    def test_latency_memory_bounding(self):
        """Ensure latencies don't grow unbounded."""
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        for i in range(1500):
            m.record_request(200, "/api/v1/test", float(i))
        snap = m.snapshot()
        # Should be bounded to ~500 after cleanup
        assert snap["endpoint_latencies"]["/api/v1/test"]["count"] <= 1000

    def test_uptime_increases(self):
        from app.monitoring import ApplicationMetrics
        m = ApplicationMetrics()
        t1 = m.uptime_seconds
        time.sleep(0.05)
        t2 = m.uptime_seconds
        assert t2 > t1

class TestGetMetricsSingleton:
    """Tests for the metrics singleton accessor."""

    def test_get_metrics_returns_same_instance(self):
        from app.monitoring import get_metrics
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2

# Deep Health Check Tests

class TestDatabaseHealthCheck:
    """Tests for the DB health check function."""

    @pytest.mark.asyncio
    async def test_healthy_database(self):
        from app.monitoring import check_database_health
        mock_result = MagicMock()
        mock_result.data = [{"id": "test"}]

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.table.return_value = mock_table

        with patch("app.database.get_supabase", return_value=mock_db):
            result = await check_database_health()

        assert result["status"] == "healthy"
        assert result["connected"] is True
        assert result["latency_ms"] is not None

    @pytest.mark.asyncio
    async def test_database_not_initialized(self):
        from app.monitoring import check_database_health
        with patch("app.database.get_supabase", side_effect=RuntimeError("Not initialized")):
            result = await check_database_health()
        assert result["status"] == "unavailable"
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        from app.monitoring import check_database_health
        with patch("app.database.get_supabase", side_effect=Exception("Connection refused")):
            result = await check_database_health()
        assert result["status"] == "unhealthy"
        assert result["connected"] is False

class TestLLMHealthCheck:
    """Tests for the LLM health check function."""

    @pytest.mark.asyncio
    async def test_groq_configured(self):
        from app.monitoring import check_llm_health
        with patch("app.monitoring.get_settings") as mock_settings:
            mock_settings.return_value.GROQ_API_KEY = "gsk_test"
            mock_settings.return_value.OPENAI_API_KEY = None
            result = await check_llm_health()
        assert result["status"] == "healthy"
        assert result["providers"]["groq"] == "configured"
        assert result["providers"]["openai"] == "not_configured"

    @pytest.mark.asyncio
    async def test_no_llm_configured(self):
        from app.monitoring import check_llm_health
        with patch("app.monitoring.get_settings") as mock_settings:
            mock_settings.return_value.GROQ_API_KEY = ""
            mock_settings.return_value.OPENAI_API_KEY = None
            result = await check_llm_health()
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_both_providers_configured(self):
        from app.monitoring import check_llm_health
        with patch("app.monitoring.get_settings") as mock_settings:
            mock_settings.return_value.GROQ_API_KEY = "gsk_test"
            mock_settings.return_value.OPENAI_API_KEY = "sk-test"
            result = await check_llm_health()
        assert result["status"] == "healthy"
        assert result["providers"]["openai"] == "configured"

class TestDeepHealthCheck:
    """Tests for the combined deep health check."""

    @pytest.mark.asyncio
    async def test_deep_health_all_healthy(self):
        from app.monitoring import deep_health_check
        with (
            patch("app.monitoring.check_database_health", new_callable=AsyncMock) as mock_db,
            patch("app.monitoring.check_llm_health", new_callable=AsyncMock) as mock_llm,
            patch("app.monitoring.get_settings") as mock_settings,
        ):
            mock_db.return_value = {"status": "healthy", "connected": True, "latency_ms": 5.0}
            mock_llm.return_value = {"status": "healthy", "providers": {"groq": "configured"}}
            mock_settings.return_value.APP_VERSION = "0.1.0"
            mock_settings.return_value.ENVIRONMENT = "testing"

            result = await deep_health_check()

        assert result["status"] == "healthy"
        assert "components" in result
        assert result["components"]["database"]["status"] == "healthy"
        assert result["components"]["llm"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_deep_health_db_unavailable_still_healthy_in_dev(self):
        from app.monitoring import deep_health_check
        with (
            patch("app.monitoring.check_database_health", new_callable=AsyncMock) as mock_db,
            patch("app.monitoring.check_llm_health", new_callable=AsyncMock) as mock_llm,
            patch("app.monitoring.get_settings") as mock_settings,
        ):
            mock_db.return_value = {"status": "unavailable", "connected": False}
            mock_llm.return_value = {"status": "healthy", "providers": {"groq": "configured"}}
            mock_settings.return_value.APP_VERSION = "0.1.0"
            mock_settings.return_value.ENVIRONMENT = "development"

            result = await deep_health_check()

        # DB unavailable is OK in dev
        assert result["status"] == "healthy"

# API Endpoint Tests

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

class TestDeepHealthEndpoint:
    """Tests for /health/deep endpoint."""

    def test_deep_health_endpoint(self):
        from app.main import app
        client = TestClient(app)
        with (
            patch("app.monitoring.check_database_health", new_callable=AsyncMock) as mock_db,
            patch("app.monitoring.check_llm_health", new_callable=AsyncMock) as mock_llm,
        ):
            mock_db.return_value = {"status": "healthy", "connected": True, "latency_ms": 5.0}
            mock_llm.return_value = {"status": "healthy", "providers": {"groq": "configured"}}
            response = client.get("/health/deep")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "uptime_seconds" in data

class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_returns_snapshot(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_errors" in data
        assert "uptime_seconds" in data
        assert "status_codes" in data
        assert "endpoint_latencies" in data
        assert "pipelines" in data

class TestRequestTracing:
    """Tests for X-Request-ID tracing middleware."""

    def test_response_includes_request_id(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert "x-request-id" in response.headers
        # Should be a UUID4
        request_id = response.headers["x-request-id"]
        assert len(request_id) == 36  # UUID format

    def test_respects_incoming_request_id(self):
        from app.main import app
        client = TestClient(app)
        custom_id = "custom-trace-12345"
        response = client.get("/health", headers={"x-request-id": custom_id})
        assert response.headers["x-request-id"] == custom_id

    def test_generates_unique_ids(self):
        from app.main import app
        client = TestClient(app)
        ids = set()
        for _ in range(10):
            response = client.get("/health")
            ids.add(response.headers["x-request-id"])
        assert len(ids) == 10  # All unique

# Production Config Validation Tests

class TestProductionConfigValidation:
    """Tests for production environment config checks."""

    def test_production_requires_secret_key(self):
        from pydantic import ValidationError
        from app.config import Settings
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="short",
            )

    def test_production_accepts_valid_secret_key(self):
        from app.config import Settings
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 64,
        )
        assert s.SECRET_KEY == "a" * 64

    def test_development_allows_auto_generated_key(self):
        from app.config import Settings
        s = Settings(ENVIRONMENT="development")
        assert len(s.SECRET_KEY) >= 32

    def test_testing_allows_any_key(self):
        from app.config import Settings
        s = Settings(ENVIRONMENT="testing", SECRET_KEY="test-key")
        assert s.SECRET_KEY == "test-key"

    def test_supabase_url_requires_https(self):
        from pydantic import ValidationError
        from app.config import Settings
        with pytest.raises(ValidationError, match="HTTPS"):
            Settings(SUPABASE_URL="http://insecure.example.com")

# Gunicorn Config Validation

class TestGunicornConfig:
    """Validate gunicorn config loads without errors."""

    def test_gunicorn_config_importable(self):
        import importlib.util
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "gunicorn.conf.py",
        )
        spec = importlib.util.spec_from_file_location("gunicorn_conf", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.worker_class == "uvicorn.workers.UvicornWorker"
        assert module.workers >= 1
        assert module.timeout == 180
        assert module.preload_app is True
        assert module.max_requests == 1000

# Migration Files Existence

class TestMigrationFiles:
    """Verify all migration SQL files exist."""

    def test_all_migration_files_exist(self):
        import os
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "migrations",
        )
        expected_files = [
            "001_initial_schema.sql",
            "002_scaffolds.sql",
            "003_portfolio_outputs.sql",
        ]
        for filename in expected_files:
            path = os.path.join(migrations_dir, filename)
            assert os.path.exists(path), f"Missing migration: {filename}"

    def test_migration_files_contain_rls(self):
        """Every table must have RLS enabled."""
        import os
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "migrations",
        )
        for filename in os.listdir(migrations_dir):
            if not filename.endswith(".sql"):
                continue
            with open(os.path.join(migrations_dir, filename)) as f:
                content = f.read()
            if "CREATE TABLE" in content:
                assert "ENABLE ROW LEVEL SECURITY" in content, (
                    f"Migration {filename} creates tables without RLS"
                )

    def test_migration_002_creates_scaffolds(self):
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "migrations", "002_scaffolds.sql",
        )
        with open(path) as f:
            content = f.read()
        assert "scaffolds" in content
        assert "user_id" in content
        assert "project_title" in content
        assert "files JSONB" in content

    def test_migration_003_creates_portfolio_outputs(self):
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "migrations", "003_portfolio_outputs.sql",
        )
        with open(path) as f:
            content = f.read()
        assert "portfolio_outputs" in content
        assert "readme_markdown" in content
        assert "resume_bullets JSONB" in content
        assert "linkedin_post JSONB" in content
