# 🌐 AI Market Research Agent

> **An evidence-based market research assistant that fact-checks every finding across live web sources — with zero guesswork.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-advanceresearchh--agent--uht8.vercel.app-brightgreen?style=for-the-badge&logo=vercel)](https://advanceresearchh-agent-uht8.vercel.app)
[![Built For](https://img.shields.io/badge/Hackathon-Christ%20University-blue?style=for-the-badge)](https://advanceresearchh-agent-uht8.vercel.app)
[![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20OpenRouter-orange?style=for-the-badge)](#tech-stack)

---

## 🚀 Live Application
👉 **Try it here:** [https://advanceresearchh-agent-uht8.vercel.app](https://advanceresearchh-agent-uht8.vercel.app)

---

## 💡 The Problem

When founders, consultants, and business analysts research new markets or competitors using standard AI tools:
- **AI models make up facts** (hallucinating pricing, dates, and market sizes).
- **Outdated data is presented as current**, leading to flawed business decisions.
- **No proof is provided** — claims are made without clickable citations or verification.

---

## ✨ The Solution

Our **AI Market Research Agent** conducts real-time web research like a diligent human analyst, but in minutes. It searches live sources, verifies numbers across multiple independent pages, flags conflicting reports, and compiles a comprehensive executive report with side-by-side competitor comparisons.

```
       [ Business Question ]
                 │
                 ▼
       [ 1. Plan Research ]  ──────> Identifies key competitors & questions
                 │
                 ▼
       [ 2. Live Web Search ] ─────> Searches multiple trustworthy sources in parallel
                 │
                 ▼
       [ 3. Fact-Check & Verify ] ──> Cross-references data points across 2+ sources
                 │
                 ▼
       [ 4. Compare & Synthesize ] ─> Creates side-by-side competitor table
                 │
                 ▼
       [ 5. Verified Final Report ] ─> Ready to read, copy, or download as PDF
```

---

## 🌟 Key Features

### 1. 🔍 Multi-Source Verification
Every extracted data point is color-coded by reliability:
- 🟢 **Verified (2+ Sources)**: Independently confirmed across two or more trustworthy websites.
- 🟡 **Single Source**: Found on one reputable page with direct quotation.
- 🔴 **Disputed**: Sources report contradictory numbers.

### 2. ⚖️ Discrepancy Detection (No Blind Guessing)
When different publications report conflicting numbers (e.g. one source states ₹3,500/month while another states ₹4,200/month), the agent presents both figures side-by-side with original links rather than guessing or averaging.

### 3. 🚫 No-Guesswork Policy
If specific metrics (like private revenue or secret unit economics) aren't publicly verifiable, the agent explicitly flags them as **Information Not Found** instead of fabricating numbers.

### 4. 📊 Side-by-Side Competitor Comparison
Automatically organizes pricing, features, fleet sizes, and city availability into a clean, easy-to-read comparison table.

### 5. 📑 One-Click PDF & Markdown Export
Generate clean, board-ready executive summaries with direct clickable citations for your team or investors.

---

## 🖥️ User Experience

- **Neo-Brutalist Visual Design**: Bold, modern, high-contrast interface designed for clarity and fast decision-making.
- **Live Search Timeline**: Watch the agent plan, search, fact-check, and synthesize in real time.
- **Interactive Inspection**: Click on any metric to view the exact sentence quoted from the source page.
- **Past Research Drawer**: Revisit and compare previous research projects anytime with one click.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 16 (React, TypeScript)** | Fast, responsive interface deployed on **Vercel** |
| **Styling** | **Neo-Brutalist CSS & Tailwind** | High-contrast, clean typography, judge-friendly UX |
| **Backend** | **FastAPI (Python)** | High-performance async orchestration and endpoints |
| **AI Intelligence** | **OpenRouter** | Advanced reasoning for query planning and report writing |
| **Live Search** | **Tavily API** | Real-time web discovery and article extraction |
| **Streaming** | **Server-Sent Events (SSE)** | Live step-by-step progress tracking for users |

---

## 🏃 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/heisenberghz/advanceresearchh_agent.git
cd advanceresearchh_agent
```

### 2. Run the Backend
```bash
cd backend
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Run the Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🎯 Sample Questions To Try

Click any sample scenario right on the home page or try these:

- *"Electric scooter rental and subscription market in Bengaluru: competitors, pricing, battery swap models, and regulations."*
- *"Quick commerce delivery services in Mumbai: Blinkit vs Zepto vs Instamart delivery fees, dark store economics, and market share."*
- *"AI-powered customer service platforms: compare Zendesk, Freshdesk, and Intercom pricing tiers, features, and enterprise offerings."*

---

## 👥 Built With ❤️ For The Hackathon

- **Product:** AI Market Research Agent
- **Live URL:** [https://advanceresearchh-agent-uht8.vercel.app](https://advanceresearchh-agent-uht8.vercel.app)
