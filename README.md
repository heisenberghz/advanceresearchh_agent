# 🌐 AI Market Research Agent (ResearchOps)

> **An autonomous, evidence-grounded market intelligence agent that fact-checks every finding across live web sources — with strict provenance, multi-source verification, and zero guesswork.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-advanceresearchh--agent.vercel.app-brightgreen?style=for-the-badge&logo=vercel)](https://advanceresearchh-agent.vercel.app)
[![Built For](https://img.shields.io/badge/Hackathon-Christ%20University%20%7C%20GATEWAYS%202026-blue?style=for-the-badge)](https://advanceresearchh-agent.vercel.app)
[![Tests](https://img.shields.io/badge/Automated%20Tests-109%2F109%20Passed-success?style=for-the-badge&logo=pytest)](https://github.com/heisenberghz/advanceresearchh_agent)
[![Tech Stack](https://img.shields.io/badge/Stack-Next.js%2016%20%7C%20FastAPI%20%7C%20Supabase%20%7C%20OpenRouter-orange?style=for-the-badge)](#-complete-tech-stack)

---

## 🚀 Live Application

👉 **Live Demo:** [https://advanceresearchh-agent.vercel.app](https://advanceresearchh-agent.vercel.app)

> 💡 **Judge / Evaluator Tip:** Click the **"⚡ 1-Click EV Mobility Scenario"** button directly on the homepage to launch a full competitive research run instantly with zero typing!

---

## 💡 The Problem

When founders, consultants, and business analysts research new markets or competitors using standard LLM tools:
- **AI models hallucinate facts**: Fabricating pricing, launch dates, market shares, and unit economics.
- **Outdated data is presented as current**: Misleading strategic decisions with months-old or years-old assumptions.
- **Zero audit trail**: Claims are made without clickable citations, excerpts, or cross-source corroboration.
- **Silent guesswork on missing data**: Standard LLMs guess numbers rather than admitting when data is private or unavailable.

---

## ✨ The Solution

**ResearchOps** conducts real-time competitive intelligence like a diligent research analyst team — compressed into seconds. It dispatches autonomous sub-agents to scour live web sources in parallel, cross-verifies every single metric across 2+ independent websites, detects numeric discrepancies (>15% variance), executes bounded retries for weak claims, and compiles an executive comparison report with 100% grounded citations.

```
                         [ Business Research Question ]
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   1. PLANNER AGENT            │
                       │   Deconstructs entities &     │
                       │   creates targeted search jobs│
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   2. PARALLEL RESEARCHERS     │
                       │   Bounded concurrent searches │
                       │   via Tavily Web Search API   │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   3. FACT-CHECKER AGENT       │
                       │   Evaluates evidence trust    │
                       │   Detects numeric conflicts   │
                       └───────────────┬───────────────┘
                                       │
                      [ Evidence weak / missing? ]
                                  ├── YES ──► [ AUTONOMOUS RETRY LOOP ]
                                  │           Rewrites queries & re-researches
                                  ▼ NO
                       ┌───────────────────────────────┐
                       │   4. GAP DETECTOR & MATRIX    │
                       │   Flags missing private data  │
                       │   Builds competitor table     │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   5. SYNTHESIS WRITER AGENT   │
                       │   Executive briefing & PDF    │
                       │   with 100% clickable sources │
                       └───────────────────────────────┘
```

---

## 🌟 Key Features

### 1. 🔍 Multi-Source Trust Tagging
Every extracted data point is evaluated against strict provenance rules and color-coded:
- 🟢 **Verified (2+ Sources)**: Independently confirmed across two or more trustworthy domains.
- 🟡 **Single Source**: Found on one reputable webpage with the exact supporting excerpt quoted.
- 🔴 **Disputed**: Two or more sources report conflicting figures (variance > 15%). Both figures and links are shown side-by-side.
- ⚪ **Not Found**: Data is not publicly available. Explicitly flagged with zero guesswork.

### 2. 🔄 Autonomous Retry Loop with Query Reformulation
If initial searches return weak evidence or missing attributes, the system does not give up or hallucinate. A dedicated **Retry Coordinator** automatically rewrites the search query with targeted domain-specific modifiers and re-queries the web up to a bounded limit.

### 3. ⚖️ Discrepancy Detection & Conflict Resolution
When sources disagree (e.g. one publication reports ₹3,500/month while another reports ₹4,200/month), the agent presents both values, original excerpts, and direct links side-by-side so decision-makers can judge context.

### 4. 🚫 Strict Anti-Hallucination & "No-Guesswork" Policy
If metrics (such as private revenue or unit economics) are not publicly disclosed, the agent marks them as **Not Found Publicly** instead of fabricating plausible-sounding numbers.

### 5. 📊 Structured Side-by-Side Competitor Matrix
Automatically organizes pricing tiers, operational fleets, key attributes, and geographic presence into a clean, comparative table.

### 6. 📑 One-Click PDF & Markdown Export
Instantly generate board-ready executive summaries complete with executive takeaways, competitor matrices, and cited URLs.

---

## 🖥️ User Experience

- **Neo-Brutalist Visual Design**: High-contrast, bold, judge-friendly interface crafted with custom CSS tokens, modern typography, and responsive cards.
- **Live Search Timeline**: Watch every workflow stage (Planning $\rightarrow$ Searching $\rightarrow$ Fact-Checking $\rightarrow$ Deepening $\rightarrow$ Comparing $\rightarrow$ Final Report) update live.
- **Interactive Provenance Drawer**: Click on any metric to view the exact quoted sentence, retrieval timestamp, and URL.
- **Past Research Drawer**: Search, revisit, and inspect previous research runs persisted in the cloud database.

---

## 🛠️ Complete Tech Stack

| Layer | Technology | Version | Purpose in ResearchOps |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | **Next.js (App Router)** | `16.0+` | Fast, accessible, server/client hybrid UI deployed on **Vercel** |
| **Frontend Language** | **TypeScript** | `5.0+` | End-to-end type safety across research models, state, and API contracts |
| **Styling & Design System** | **Tailwind CSS + Neo-Brutalist System** | `4.0` | Custom tokens, 3px solid borders, vibrant badges, and micro-animations |
| **Icons & UI Utilities** | **Lucide React** | Latest | Consistent icons for trust tags, status badges, and action buttons |
| **Backend Framework** | **FastAPI** | `0.115+` | High-throughput asynchronous Python web framework |
| **Data Validation & Schemas** | **Pydantic v2** | `2.10+` | Strict request/response validation, domain models, and JSON schema enforcement |
| **Database & Persistence** | **Supabase (PostgreSQL)** | Cloud | Cloud database persisting research runs, jobs, facts, citations, and query cache |
| **AI Intelligence / LLMs** | **OpenRouter API** | Cloud | Multi-model routing: `deepseek-chat` for fast extraction, `claude-3.5-sonnet` for executive report synthesis |
| **Live Web Discovery** | **Tavily Search API** | Cloud | Real-time web discovery, article extraction, and persistent connection pooling |
| **Real-Time Streaming** | **Server-Sent Events (SSE)** | Native HTTP | Sub-second real-time timeline progress streaming to the browser |
| **Testing & Quality** | **Pytest & AnyIO** | `9.1+` | **109 automated tests** covering unit logic, workflow pipelines, and live scenarios |
| **Deployment & Hosting** | **Vercel & Render** | Cloud | Global Edge CDN (Frontend) + Containerized ASGI Cloud Service (Backend) |

---

## 🏃 Quick Start (Local Setup)

### Prerequisites
- Node.js `18.0+` & npm
- Python `3.11+`
- API Keys: [Tavily](https://tavily.com), [OpenRouter](https://openrouter.ai), and [Supabase](https://supabase.com)

### 1. Clone the repository
```bash
git clone https://github.com/heisenberghz/advanceresearchh_agent.git
cd advanceresearchh_agent
```

### 2. Configure & Run Backend
```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment keys
cp .env.example .env
# Edit backend/.env and add your TAVILY_API_KEY, OPENROUTER_API_KEY, and SUPABASE credentials

# Run automated tests (109 passing)
pytest

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 3. Configure & Run Frontend
```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🎯 Sample Questions To Try

You can test with any market research query or click the **1-Click Preset** on the homepage:

- *"Electric scooter rental and subscription market in Bengaluru: competitors, pricing, battery swap models, and regulations."*
- *"Quick commerce delivery services in Mumbai: Blinkit vs Zepto vs Instamart delivery fees, dark store economics, and market share."*
- *"AI-powered customer service platforms: compare Zendesk, Freshdesk, and Intercom pricing tiers, features, and enterprise offerings."*

---

## 👥 Built With ❤️ For The Hackathon

- **Product:** ResearchOps — AI Market Research Agent
- **Event:** Christ University Hackathon / GATEWAYS 2026
- **Live URL:** [https://advanceresearchh-agent.vercel.app](https://advanceresearchh-agent.vercel.app)
