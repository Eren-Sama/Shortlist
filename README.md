<div align="center">

# ⚡ Shortlist  
### Engineer Your Career Signal

An AI-powered multi-agent system that reverse-engineers job descriptions and generates recruiter-aligned projects, repositories, and portfolio assets.

<br/>

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blueviolet?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 🧠 Overview

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

# 🧩 Intelligence System

Shortlist operates as a coordinated graph of specialized agents:

### 🔍 JD Analysis  
Extracts required skills, seniority expectations, domain context, and implicit behavioral signals.

### 🏢 Company Logic Engine  
Applies contextual modifiers based on company archetype:
- Startup → velocity, ownership
- Enterprise → scale, reliability
- Consultancy → clarity, adaptability

### 🏗 Capstone Generator  
Produces strategically aligned project ideas with recruiter-match scoring.

### 📊 Repository Analyzer  
Evaluates GitHub repositories for:
- Structural quality  
- Documentation clarity  
- Signal strength  
- Alignment vs target role  

### 🧱 Scaffold Generator  
Generates structured production-grade repository blueprints.

### 📈 Portfolio Optimizer  
Creates:
- Optimized README copy  
- Resume bullets  
- Demo pitch script  
- Social launch copy  

### 📄 Resume Fitness Scorer  
Analyzes resume alignment against JD graph and surfaces improvement gaps.

---

# 🏗 Architecture

```
                         ┌────────────────────┐
                         │   Reverse Proxy    │
                         │   TLS Termination  │
                         └─────────┬──────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
      ┌─────▼─────┐          ┌─────▼─────┐         ┌─────▼─────┐
      │  Frontend │          │  Backend  │         │ External  │
      │  Next.js  │          │  FastAPI  │         │ Services  │
      │  AppRouter│          │ LangGraph │         │           │
      └───────────┘          └─────┬─────┘         └─────┬─────┘
                                    │                     │
                              ┌─────▼─────┐         ┌─────▼─────┐
                              │ PostgreSQL│         │    LLM    │
                              │  + Auth   │         │  Provider │
                              └───────────┘         └───────────┘
```

---

# ⚙️ Tech Stack

| Layer | Technology |
|--------|------------|
| Frontend | Next.js (App Router), React, TypeScript, Tailwind |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| AI Orchestration | LangGraph |
| LLM | Groq (Llama 3.x series) |
| Database | PostgreSQL with Row-Level Security |
| Infrastructure | Docker multi-stage builds |
| CI/CD | GitHub Actions |
| Testing | Comprehensive automated test suite |

---

# 📂 Structural Design

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

# 🔥 Engineering Highlights

- Graph-based multi-agent orchestration  
- Provider-agnostic LLM abstraction layer  
- Strict schema validation  
- Database-level security enforcement  
- Structured logging architecture  
- Production-grade containerization  
- Clean separation of concerns  

---

# 🎯 Design Philosophy

- Signal-first engineering  
- Modular intelligence layers  
- Production-ready architecture  
- Recruiter-readable system design  
- Scalable orchestration patterns  

---

# 🔎 Repository Note

This repository is shared publicly for architectural demonstration and portfolio review purposes.

Operational configuration details and deployment layers are intentionally not included.

---

# 📜 License

MIT

---

<div align="center">

Built as strategic career infrastructure.

</div>
