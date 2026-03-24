# ──────────────────────────────────────────────
# Shortlist Backend — HuggingFace Spaces Dockerfile
# Deploys FastAPI backend as a Docker Space
# ──────────────────────────────────────────────

# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

# HuggingFace Spaces requires UID 1000
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Install git (needed for repo analyzer feature)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Copy backend application code
COPY --chown=user backend/app/ ./app/
COPY --chown=user backend/migrations/ ./migrations/
COPY --chown=user backend/apply_migration.py ./apply_migration.py

# Create temp directory for repo cloning
RUN mkdir -p /tmp/shortlist_repos && \
    chown user:user /tmp/shortlist_repos && \
    chmod 700 /tmp/shortlist_repos

# Switch to non-root user
USER user

ENV PATH="/home/user/.local/bin:$PATH"

# HuggingFace Spaces MUST listen on port 7860
EXPOSE 7860

# Run with uvicorn — single worker for HF free tier
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--workers", "2", \
     "--timeout-keep-alive", "120"]
