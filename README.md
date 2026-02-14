# Shortlist

An AI agent system that reverse-engineers what recruiters look for, then helps you build exactly that — tailored capstone projects, polished repos, and optimized portfolio materials, all calibrated to a specific job description.

---

## What It Does

Paste a job description and Shortlist runs it through a pipeline of specialized AI agents:

1. **JD Analysis** — Extracts skills, role level, domain context, and what the company actually cares about
2. **Company Logic** — Applies behavioral modifiers based on company type (startup hustle vs. FAANG system design vs. consultancy breadth)
3. **Capstone Generator** — Proposes 3 project ideas engineered to hit the skills the JD demands, each with resume bullets and a recruiter-match score
4. **Repo Analyzer** — Scores any GitHub repo on structure, documentation, code quality, and how it reads to a non-technical recruiter
5. **Scaffold Generator** — Outputs a production-ready repo skeleton (directory tree, configs, starter code) for any selected project
6. **Portfolio Optimizer** — Generates README copy, resume bullets, a 60-second demo script, and a LinkedIn post for each project
7. **Resume Fitness Scorer** — Compares your existing resume against the JD analysis and scores the match with specific improvement suggestions

## Architecture

```
                                              ┌──────────────────┐
                                              │  Nginx / Caddy   │
                                              │  (TLS + Proxy)   │
                                              └────┬────────┬────┘
                                                   │        │
                                        ┌──────────▼──┐  ┌──▼───────────┐
                                        │   Backend   │  │   Frontend   │
                                        │  (Gunicorn  │  │  (Next.js    │
                                        │   +Uvicorn) │  │  Standalone) │
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

The backend is a FastAPI service running a LangGraph agent orchestrator. Each "intelligence layer" is an independent graph node — the orchestrator wires them together based on what the user requests. The frontend is a Next.js App Router dashboard with Supabase auth (Google OAuth + magic link).

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS v4 |
| Backend | FastAPI, Pydantic v2, Python 3.12 |
| AI Orchestration | LangGraph, langchain-groq |
| LLM | Groq (Llama 3.3 70B) |
| Database + Auth | Supabase (PostgreSQL + Row Level Security + Auth) |
| Deployment | Docker (multi-stage), Gunicorn + Uvicorn, GitHub Actions CI/CD |

## Project Structure

```
Shortlist/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── nodes/          # 7 LangGraph nodes (jd, company, capstone,
│   │   │   │                   #   repo, scaffold, portfolio, fitness)
│   │   │   ├── orchestrator.py # Graph builder + pipeline routing
│   │   │   └── state.py        # Shared state schema
│   │   ├── api/v1/             # 6 REST endpoint modules
│   │   ├── llm/provider.py     # Provider-agnostic LLM factory
│   │   ├── prompts/            # 7 system/user prompt templates
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # DB operations + GitHub analyzer
│   │   ├── config.py           # Env-based settings (validated)
│   │   ├── database.py         # Supabase async client
│   │   ├── logging_config.py   # Structured JSON logging
│   │   ├── main.py             # App factory + middleware stack
│   │   ├── monitoring.py       # Health checks + Prometheus metrics
│   │   └── security.py         # CORS, rate limiting, security headers
│   ├── migrations/             # 4 SQL schema migrations
│   ├── tests/                  # 171 pytest tests (10 modules)
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Landing page (WebGL + animations)
│   │   │   └── dashboard/          # 8 authenticated routes
│   │   │       ├── analyze/        # JD analysis form
│   │   │       ├── results/[id]/   # Analysis results + capstones
│   │   │       ├── repo/           # Repo analyzer + results
│   │   │       ├── scaffold/       # Scaffold generator + viewer
│   │   │       ├── portfolio/      # Portfolio optimizer output
│   │   │       ├── fitness/        # Resume fitness scorer
│   │   │       ├── projects/       # Saved projects overview
│   │   │       └── profile/        # User profile + avatar
│   │   ├── components/             # Auth, landing (WebGL), UI primitives
│   │   ├── lib/                    # API client, Supabase client, utils
│   │   └── middleware.ts           # Route protection
│   ├── Dockerfile
│   └── package.json
├── .github/workflows/ci.yml       # 4-job CI/CD pipeline
├── Makefile                        # Dev/test/lint shortcuts
└── DEPLOY.md                       # Production deployment guide
```

## License

MIT
