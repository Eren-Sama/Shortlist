<div align="center">

# Shortlist

### Engineer Career Signal with Precision

An AI-powered multi-agent system that reverse-engineers job descriptions  
and constructs recruiter-aligned projects, repositories, and portfolio assets.

<br/>

<p>
  <img src="https://img.shields.io/badge/Next.js-000?style=flat-square&logo=nextdotjs&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-000?style=flat-square&logo=react&logoColor=61DAFB"/>
  <img src="https://img.shields.io/badge/TypeScript-000?style=flat-square&logo=typescript&logoColor=3178C6"/>
  <img src="https://img.shields.io/badge/FastAPI-000?style=flat-square&logo=fastapi&logoColor=009688"/>
  <img src="https://img.shields.io/badge/Python-000?style=flat-square&logo=python&logoColor=3776AB"/>
  <img src="https://img.shields.io/badge/PostgreSQL-000?style=flat-square&logo=postgresql&logoColor=336791"/>
  <img src="https://img.shields.io/badge/Docker-000?style=flat-square&logo=docker&logoColor=2496ED"/>
  <img src="https://img.shields.io/badge/LangGraph-MultiAgent-000?style=flat-square"/>
</p>

</div>

---

## Philosophy

Recruiters don’t reward randomness.  
They reward alignment.

Shortlist converts a job description into a structured skill graph,  
then engineers everything around that graph.

Projects.  
Repositories.  
Resume bullets.  
Portfolio positioning.

All calibrated to the signal the role demands.

---

# System Design

Shortlist is built as a modular, graph-orchestrated intelligence system.

Each capability is an independent node wired dynamically at runtime.

```
                         ┌────────────────────┐
                         │   Reverse Proxy    │
                         │   TLS Termination  │
                         └─────────┬──────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
          ┌─────▼─────┐      ┌─────▼─────┐      ┌────▼────┐
          │ Frontend  │      │  Backend  │      │ External │
          │ Next.js   │      │  FastAPI  │      │ Services │
          │ AppRouter │      │ LangGraph │      │          │
          └───────────┘      └─────┬─────┘      └────┬────┘
                                    │                │
                               ┌────▼────┐      ┌────▼────┐
                               │ Postgres │      │   LLM   │
                               │  + Auth  │      │ Provider│
                               └──────────┘      └─────────┘
```

---

# Intelligence Graph

Shortlist operates through specialized agents:

- **JD Analyzer** — extracts explicit + implicit hiring signals  
- **Company Logic Layer** — applies contextual behavioral weighting  
- **Capstone Engine** — generates strategically aligned project blueprints  
- **Repository Analyzer** — evaluates signal clarity & recruiter readability  
- **Scaffold Generator** — produces production-grade structural foundations  
- **Portfolio Optimizer** — crafts narrative positioning & demo scripts  
- **Resume Fitness Engine** — measures alignment delta vs target role  

Each node operates independently.  
The orchestrator composes them based on user intent.

---

# Technical Foundation

| Layer | Stack |
|--------|--------|
| Frontend | Next.js (App Router), React, TypeScript |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| AI Orchestration | LangGraph (graph-based agent routing) |
| LLM | Groq (Llama 3.x series) |
| Data Layer | PostgreSQL with Row-Level Security |
| Infra | Multi-stage Docker builds |
| CI/CD | GitHub Actions |
| Testing | Extensive automated test coverage |

---

# Structural Layout

```
Shortlist/
├── backend/
│   ├── agents/
│   ├── api/
│   ├── services/
│   ├── llm/
│   ├── prompts/
│   ├── schemas/
│   ├── monitoring.py
│   ├── security.py
│   └── main.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── middleware.ts
│
├── CI workflows
├── Docker configuration
└── Deployment documentation
```

---

# Engineering Characteristics

- Graph-based multi-agent orchestration  
- Strict schema validation and typed boundaries  
- Provider-agnostic LLM abstraction  
- Database-level security enforcement  
- Structured logging architecture  
- Containerized production pipeline  
- Clear separation of system concerns  

---

# Design Intent

Shortlist is not a template generator.

It is signal infrastructure.

It formalizes:
- How hiring signals are interpreted  
- How project narratives are engineered  
- How alignment gaps are quantified  

---

# Repository Note

This repository is shared for architectural demonstration and portfolio review.

Operational configuration and deployment layers are intentionally not included.

---

# License

MIT

---

<div align="center">

Built with intent.  
Engineered for leverage.

</div>
