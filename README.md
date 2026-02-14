<div align="center">

# ⚡ Shortlist  
### Engineer Your Career Signal

An AI multi-agent system that reverse-engineers job descriptions and generates recruiter-aligned projects, repositories, and portfolio assets.

</div>

---

## 🧠 Concept

Recruiters evaluate signal alignment — not randomness.

Shortlist transforms a job description into a structured skill graph, then engineers projects, repositories, and resume materials optimized for that exact role.

This system is built as a modular, production-grade multi-agent architecture.

---

# 🧩 Intelligence Architecture

Shortlist operates as a coordinated graph of independent intelligence nodes:

- JD Analysis  
- Company Logic Engine  
- Capstone Generator  
- Repository Analyzer  
- Scaffold Generator  
- Portfolio Optimizer  
- Resume Fitness Scorer  

Each node operates independently and is orchestrated dynamically depending on user intent.

---

# 🏗 System Architecture

```
                         ┌────────────────────┐
                         │  Reverse Proxy     │
                         │  TLS Termination   │
                         └─────────┬──────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
      ┌─────▼─────┐          ┌─────▼─────┐         ┌─────▼─────┐
      │  Frontend │          │  Backend  │         │ External  │
      │  Next.js  │          │ FastAPI   │         │ Services  │
      │  AppRouter│          │ LangGraph │         │           │
      └───────────┘          └─────┬─────┘         └─────┬─────┘
                                    │                     │
                              ┌─────▼─────┐         ┌─────▼─────┐
                              │ Database  │         │   LLM     │
                              │ + Auth    │         │ Provider  │
                              └───────────┘         └───────────┘
```

---

# ⚙️ Technical Stack

| Layer | Stack |
|--------|--------|
| Frontend | Next.js (App Router), React, TypeScript |
| Backend | FastAPI, Python 3.12 |
| AI Orchestration | LangGraph |
| LLM | Groq (Llama 3.x series) |
| Database | PostgreSQL with Row-Level Security |
| Infrastructure | Dockerized multi-stage builds |
| Testing | Comprehensive automated test suite |

---

# 📂 Structural Overview

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
├── CI/CD workflows
├── Docker configuration
└── Deployment documentation
```

---

# 🔥 Engineering Highlights

- Graph-based multi-agent orchestration
- Provider-agnostic LLM abstraction
- Strict schema validation (Pydantic v2)
- Row-Level Security enforced at the database layer
- Structured JSON logging
- Production-grade monitoring hooks
- Containerized deployment pipeline
- Extensive automated testing coverage

---

# 🎯 Design Principles

- Signal-first engineering  
- Modular intelligence layers  
- Production-readiness by default  
- Clear separation of concerns  
- Recruiter-readable architecture  

---

# 🔐 Repository Notice

This repository is shared publicly for portfolio demonstration and architectural review purposes only.

Execution details, configuration layers, environment specifications, and deployment instructions are intentionally omitted.

---

# 📜 License

© 2026. All Rights Reserved.

Unauthorized copying, modification, distribution, or commercial use of this codebase is prohibited without explicit written permission from the author.

---

<div align="center">

Built as strategic career infrastructure.

</div>
