# ──────────────────────────────────────────────
# Shortlist Backend — Production Dockerfile
# Multi-stage build for minimal attack surface
# ──────────────────────────────────────────────

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim AS production

# Security: Run as non-root user
RUN groupadd -r shortlist && useradd -r -g shortlist -d /app -s /sbin/nologin shortlist

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Security: Remove unnecessary packages and caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    pip cache purge 2>/dev/null || true

# Security: Set restrictive file permissions
RUN chown -R shortlist:shortlist /app && \
    chmod -R 550 /app

# Create temp directory for repo cloning with restricted permissions
RUN mkdir -p /tmp/shortlist_repos && \
    chown shortlist:shortlist /tmp/shortlist_repos && \
    chmod 700 /tmp/shortlist_repos

# Switch to non-root user
USER shortlist

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

EXPOSE 8000

# Run with production settings
# - workers: 4 (adjust based on CPU cores)
# - timeout: 120s (repo analysis can take time)
# - limit-concurrency: prevent resource exhaustion
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", $PORT, \
     "--workers", "4", \
     "--timeout-keep-alive", "120", \
     "--limit-concurrency", "100", \
     "--no-access-log"]
