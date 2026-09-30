# ResearchOps — The Autonomous Research Agent

**Project:** GATEWAYS 2026  
**Team:** Reservoir Dogs  
**Domain:** Enterprise & Business Operations  
**Version:** 1.0  

ResearchOps is an autonomous AI research system that plans research from business queries, collects evidence via parallel search, independently verifies facts with deterministic trust tags, explicitly tracks conflicts and gaps, generates comparison matrices, and produces traceable reports.

---

## Core Product Principle

> **ResearchOps should not only provide answers. It should show the evidence behind those answers and make uncertainty visible.**

```text
QUESTION
   ↓
PLANNER
   ↓
PARALLEL RESEARCH
   ↓
EVIDENCE
   ↓
CHECKER
   ↓
┌──────────────────────────┐
│ Verified Facts           │
│ Conflicting Facts        │
│ Research Gaps            │
└────────────┬─────────────┘
             ↓
         COMPARER
             ↓
          WRITER
             ↓
      TRACEABLE REPORT
```

---

## Project Structure

```text
researchops/
├── backend/            # FastAPI backend & LangGraph research orchestration
├── frontend/           # Next.js UI (TypeScript, Tailwind CSS, shadcn/ui)
├── .gitignore          # Root ignore for secrets, node_modules, and virtualenvs
├── prd.md              # Product Requirements Document
├── tech_spec.md        # Technical Specification
├── agent_tasks.md      # Step-by-step 44-task execution plan
└── README.md           # Project documentation and developer guide
```

---

## Technology Stack & Responsibilities

| Component | Technology | Responsibility |
|---|---|---|
| **Frontend** | Next.js (TypeScript, Tailwind CSS, shadcn/ui) | User interaction, research trigger, live progress visualizer, report/source inspection, exports |
| **Backend** | Python, FastAPI | REST endpoints, Server-Sent Events (SSE) streaming, database persistence, security layer |
| **Orchestration** | LangGraph | State graph execution (`Planner` → `Researcher` → `Checker` → `Retry` → `Comparer` → `Writer`) |
| **Web Search** | Tavily API | Source discovery and web evidence retrieval |
| **LLM Gateway** | OpenRouter | Research/Checker model (cost-efficient) & Writer model (high-quality reasoning) |
| **Database** | Supabase (PostgreSQL) | Persistence of runs, jobs, facts, sources, conflicts, gaps, and reports |

---

## Environment Prerequisites

- **Python**: `>= 3.11` (Python `3.14.3` detected)
- **Node.js**: `>= 18.0.0` (Node `v24.15.0`, npm `12.0.2` detected)
- **Git**

---

## Development Setup

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev -- -p 3000
```

---

## Architecture Boundaries & Rules

1. **Security**: API keys (`OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_KEY`) must strictly reside on the backend and are never sent to the browser.
2. **Provenance**: Every fact extracted must preserve its source URL, verbatim supporting evidence snippet, and retrieval timestamp.
3. **No Fabrication**: Missing information must be recorded as an explicit `ResearchGap`.
4. **No Silent Drops**: Conflicting information between sources must be preserved in a `Conflict` record.
5. **Deterministic Trust**: Facts are tagged 🟢 GREEN, 🟡 YELLOW, or 🔴 RED based on explicit verification rules, not arbitrary model opinion.
