# Shortlist — Production Deployment Guide

This guide covers deploying Shortlist to a production environment.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Docker + Docker Compose | 24.x+ / 2.x+ |
| Supabase project | Active with tables migrated |
| Groq API key | Active account |
| Domain + SSL certificate | For HTTPS (optional for staging) |

---

## 1. Environment Setup

### Backend Environment

```bash
cd backend
cp .env.example .env
```

Fill in production values:

```dotenv
ENVIRONMENT=production
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(64))">
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_KEY=<your-service-key>
SUPABASE_JWT_SECRET=<your-jwt-secret>
GROQ_API_KEY=<your-groq-key>
```

> **CRITICAL**: `SECRET_KEY` must be explicitly set and ≥ 32 characters in production.
> The app will refuse to start without it.

### Frontend Environment

```bash
cd frontend
cp .env.example .env.local
```

```dotenv
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

---

## 2. Database Migrations

Apply all migrations to your Supabase project:

```bash
cd backend
python apply_migration.py
```

Or apply individually via the Supabase SQL editor:

```
migrations/001_initial_schema.sql    — Core tables (jd_analyses, capstone_projects, repo_analyses)
migrations/002_scaffolds.sql         — Scaffold generator table
migrations/003_portfolio_outputs.sql — Portfolio optimizer table
```

All tables have:
- UUID primary keys
- `user_id` foreign key to `auth.users`
- Row Level Security (RLS) enabled
- Service role bypass policies
- `updated_at` auto-trigger

---

## 3. Docker Deployment

### Build and Start

```bash
# Production deployment (from project root)
docker-compose -f docker-compose.prod.yml up --build -d

# Or using Make
make deploy
```

### Verify

```bash
# Health check
curl http://localhost:8000/health

# Deep health check (DB + LLM status)
curl http://localhost:8000/health/deep

# Application metrics
curl http://localhost:8000/metrics

# Frontend
curl http://localhost:3000
```

### Logs

```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## 4. Architecture

```
                    ┌──────────────────┐
                    │  Nginx / Caddy   │
                    │  (TLS + Proxy)   │
                    └────┬────────┬────┘
                         │        │
              ┌──────────▼──┐  ┌──▼──────────┐
              │   Backend   │  │   Frontend   │
              │  (Gunicorn  │  │  (Node.js    │
              │   +Uvicorn) │  │   Standalone)│
              │  Port 8000  │  │  Port 3000   │
              └──────┬──────┘  └──────────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
    ┌─────▼─────┐ ┌──▼───┐ ┌───▼────┐
    │ Supabase  │ │ Groq │ │ GitHub │
    │ (DB+Auth) │ │ (LLM)│ │  API   │
    └───────────┘ └──────┘ └────────┘
```

### Backend Container

- **Image**: `python:3.12-slim` (multi-stage, ~150MB)
- **Server**: Uvicorn with 4 workers (default)
- **Resources**: 2 CPU / 2GB RAM limit
- **Health check**: `GET /health` every 30s

### Frontend Container

- **Image**: `node:20-alpine` (standalone, ~100MB)
- **Server**: Next.js standalone Node.js server
- **Resources**: 1 CPU / 512MB RAM limit

---

## 5. Monitoring

### Endpoints

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /health` | Lightweight LB health check | Public |
| `GET /health/deep` | DB + LLM connectivity check | Public (protect in prod) |
| `GET /metrics` | Request counts, latencies, error rates | Public (protect in prod) |

### Request Tracing

Every request gets an `X-Request-ID` header:
- If your reverse proxy sends one, we'll use it
- Otherwise, a UUID4 is generated
- Response includes the same `X-Request-ID` for correlation
- Slow requests (> 5s) are logged with the request ID

### Logged Metrics

- Request count per endpoint
- Latency percentiles (p50, p95, p99)
- HTTP status code distribution
- Pipeline execution counts and error rates

### Recommended Monitoring Stack

| Tool | Purpose |
|---|---|
| **Sentry** | Error tracking + alerting |
| **Grafana + Prometheus** | Metrics dashboards |
| **Datadog / CloudWatch** | Log aggregation (JSON structured logs) |
| **Uptime Robot** | External uptime monitoring |

---

## 6. Security Checklist

- [x] All API endpoints require JWT authentication
- [x] IDOR protection on all update operations
- [x] Error messages sanitized (no internal details leaked)
- [x] RLS enabled on all tables
- [x] CORS restricted to explicit origins
- [x] Rate limiting (60 req/min default)
- [x] Request size limiting (10MB)
- [x] Security headers (CSP, HSTS, X-Frame-Options)
- [x] Non-root container user
- [x] SECRET_KEY required in production
- [x] Docs/OpenAPI disabled in production
- [x] Frontend middleware for route protection
- [x] Input sanitization on all request schemas

---

## 7. Scaling

### Horizontal Scaling

```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up --scale backend=3 -d
```

### Performance Tuning

| Config | Default | Description |
|---|---|---|
| `WEB_CONCURRENCY` | 4 | Gunicorn workers |
| `RATE_LIMIT_PER_MINUTE` | 60 | Per-IP rate limit |
| `MAX_REQUEST_SIZE_MB` | 10 | Max request body |
| `REPO_CLONE_TIMEOUT_SECONDS` | 120 | Git clone timeout |
| `LLM_MAX_TOKENS` | 4096 | Max LLM response tokens |

### Future Considerations

- **Redis**: For rate limiting, LLM response caching, session storage
- **Celery/ARQ**: Background job queue for long-running analyses
- **CDN**: CloudFront/Cloudflare for frontend static assets
- **Read Replicas**: Supabase connection pooling for high read loads

---

## 8. Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Roll back to previous images
docker tag shortlist-backend:previous shortlist-backend:latest
docker tag shortlist-frontend:previous shortlist-frontend:latest

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

---

## 9. Troubleshooting

| Issue | Solution |
|---|---|
| Backend won't start | Check `SECRET_KEY` is set in .env |
| DB connection fails | Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` |
| LLM calls failing | Check `GROQ_API_KEY` is valid |
| Frontend can't reach backend | Check `NEXT_PUBLIC_API_URL` and CORS origins |
| Docker build fails | Check `package-lock.json` exists for frontend |
| Slow responses | Check `/metrics` for p95 latencies, scale workers |
