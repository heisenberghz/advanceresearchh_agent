
## 1. High-Level Workflow

```
                         ┌─────────────────────┐
                         │       USER          │
                         │ Business Question   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      PLANNER        │
                         │ Understand Question │
                         │ Identify Assumptions│
                         │ Create Research Jobs │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                  ┌──────────────┐      ┌──────────────┐
                  │  Researcher  │      │  Researcher  │
                  │    Agent 1   │ ...  │    Agent N   │
                  └──────┬───────┘      └──────┬───────┘
                         │                     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       CHECKER       │
                         │                     │
                         │ • Source exists?    │
                         │ • Recent enough?    │
                         │ • Reliable source?  │
                         │ • Sources agree?    │
                         │ • Evidence valid?   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                  Weak / Missing /       Verified Facts
                  Conflicting Evidence        │
                         │                    │
                         ▼                    │
                  ┌──────────────┐            │
                  │   RESEARCH   │────────────┘
                  │   RETRY LOOP │
                  └──────────────┘
                         │
                         │ Max retry limit
                         ▼
                 ┌──────────────────┐
                 │ VERIFIED FACTS + │
                 │ CONFLICTS + GAPS │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    COMPARER      │
                 │                  │
                 │ Side-by-side     │
                 │ comparison table │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │     WRITER       │
                 │                  │
                 │ Summary          │
                 │ Comparison       │
                 │ Detailed findings│
                 │ Sources          │
                 └────────┬─────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │      FINAL REPORT       │
              │                         │
              │ 🟢 Trusted              │
              │ 🟡 Needs caution        │
              │ 🔴 Weak / unsupported   │
              │                         │
              │ + Conflicts             │
              │ + Gaps                  │
              │ + Source links          │
              └────────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │      USER       │
                  │ View / Download │
                  │ PDF / Markdown  │
                  └─────────────────┘
```

---

# 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND — NEXT.JS                         │
│                                                                     │
│  ┌─────────────────┐   ┌─────────────────────────────────────────┐ │
│  │ Question Input  │   │          Live Research Dashboard        │ │
│  │                 │   │                                         │ │
│  │ Business Query  │   │ Planner      ● Completed                │ │
│  │        [Start]  │   │ Researchers ● Running                   │ │
│  └────────┬────────┘   │ Checker      ○ Waiting                  │ │
│           │            │ Comparer     ○ Waiting                  │ │
│           │            │ Writer       ○ Waiting                  │ │
│           │            └─────────────────────────────────────────┘ │
│           │                                                        │
│           │            ┌─────────────────────────────────────────┐ │
│           └───────────►│             Final Report                │ │
│                        │ Summary / Table / Evidence / Conflicts  │ │
│                        └─────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                     HTTP + Streaming
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND — FASTAPI                          │
│                                                                     │
│                    ┌───────────────────────┐                        │
│                    │   Research API       │                        │
│                    │                       │                        │
│                    │ Start Research       │                        │
│                    │ Get Research Status  │                        │
│                    │ Get Report           │                        │
│                    │ Export Report        │                        │
│                    └───────────┬───────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                    ┌───────────────────────┐                        │
│                    │      LANGGRAPH        │                        │
│                    │   Agent Orchestrator  │                        │
│                    └───────────┬───────────┘                        │
│                                │                                    │
│             ┌──────────────────┼──────────────────┐                 │
│             │                  │                  │                 │
│             ▼                  ▼                  ▼                 │
│       ┌───────────┐      ┌────────────┐     ┌─────────────┐        │
│       │  PLANNER  │      │ RESEARCHER │     │   CHECKER   │        │
│       │   Agent   │      │   Agents   │     │    Agent    │        │
│       └───────────┘      └─────┬──────┘     └──────┬──────┘        │
│                                │                   │                │
│                                │                   │                │
│                                ▼                   │                │
│                         ┌──────────────┐           │                │
│                         │    TAVILY    │◄──────────┘                │
│                         │ Search/Web   │                            │
│                         └──────────────┘                            │
│                                                                     │
│                    ┌───────────────────────┐                        │
│                    │      COMPARER         │                        │
│                    │        Agent          │                        │
│                    └───────────┬───────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                    ┌───────────────────────┐                        │
│                    │       WRITER          │                        │
│                    │        Agent          │                        │
│                    └───────────┬───────────┘                        │
│                                │                                    │
│                                ▼                                    │
│                         Final Report                                │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
          ┌────────────┴─────────────┐
          │                          │
          ▼                          ▼
┌─────────────────────┐     ┌────────────────────────┐
│     SUPABASE        │     │      OPENROUTER        │
│     PostgreSQL      │     │                        │
│                     │     │  DeepSeek → Research   │
│ • Research jobs     │     │  Strong model → Write  │
│ • Facts             │     │                        │
│ • Sources           │     └────────────────────────┘
│ • Reports           │
│ • Research results  │
└─────────────────────┘
```

---

# 3. Agent Responsibilities

|Agent|Responsibility|Output|
|---|---|---|
|🧠 **Planner**|Understand the business question and break it into research jobs|Structured research plan|
|🔎 **Researchers**|Search the web and collect evidence for individual jobs|Facts + sources + evidence|
|🛡️ **Checker**|Verify evidence, freshness, source quality and conflicts|Verified facts + trust status + conflicts|
|🔄 **Retry Loop**|Send weak/missing evidence back for another search|Improved evidence|
|📊 **Comparer**|Organize verified facts into comparable entities/metrics|Comparison table|
|✍️ **Writer**|Turn verified information into a readable report|Final report|

---

# 4. Data Flow

The important part is that **raw research should not directly become the final report**.

```
User Question
      │
      ▼
Research Plan
      │
      ▼
Research Jobs
      │
      ▼
Raw Evidence
      │
      ▼
Extracted Facts
      │
      ▼
Verification
      │
      ├──────────────► Conflicts
      │
      ├──────────────► Gaps
      │
      ▼
Verified Facts
      │
      ▼
Comparison
      │
      ▼
Report Generation
      │
      ▼
Final Report
```

This gives us a clean separation:

**Search → Evidence → Verification → Presentation**

rather than:

**Search → LLM summary → Trust it**

---

# 5. Fact Verification Model

Each important fact should conceptually move through:

```
                  ┌───────────────┐
                  │   New Fact    │
                  └───────┬───────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Source Present? │
                 └───────┬─────────┘
                         │
                ┌────────┴────────┐
               NO                 YES
                │                  │
                ▼                  ▼
             🔴 RED        ┌────────────────┐
                           │ Evidence Valid?│
                           └───────┬────────┘
                                   │
                                   ▼
                           ┌────────────────┐
                           │ Recent Enough? │
                           └───────┬────────┘
                                   │
                                   ▼
                           ┌────────────────┐
                           │ Sources Agree? │
                           └───────┬────────┘
                                   │
                         ┌─────────┴─────────┐
                       YES                   NO
                        │                     │
                        ▼                     ▼
                   🟢 GREEN             🟡/🔴 FLAG
                                              │
                                              ▼
                                         Show Conflict
```

The exact trust-tag rules should be **deterministic and explicit**, rather than asking an LLM to arbitrarily decide whether something "feels trustworthy."

---

# 6. Handling Changes During Research

One of the stronger architectural features is incremental re-research.

Example:

```
Original Question
       │
       ▼
Companies: A + B + C
       │
       ▼
Research Jobs
A ── B ── C
       │
       ▼
User: "Also add Company D"
       │
       ▼
Planner detects affected work
       │
       ├── A → KEEP
       ├── B → KEEP
       ├── C → KEEP
       └── D → NEW RESEARCH
                     │
                     ▼
              Research D only
                     │
                     ▼
              Rebuild comparison
                     │
                     ▼
               Update report
```

The important idea is:

> **Existing verified work is reusable state, not disposable intermediate output.**

---

# 7. Supporting Infrastructure

```
                    ┌──────────────────┐
                    │    Next.js UI    │
                    └────────┬─────────┘
                             │
                       API + Stream
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    LangGraph     │
                    │ Workflow/State    │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     OpenRouter           Tavily            Supabase
       Models           Web Search          Database
          │                  │                  │
          ▼                  ▼                  ▼
      Reasoning          Evidence           Persistence
```

### Cost-control layer

```
                Research Request
                       │
                       ▼
                 Check Cache
                  /       \
               HIT         MISS
                │            │
                ▼            ▼
          Reuse Result    Tavily Search
                │            │
                │            ▼
                │        Save Result
                │            │
                └──────┬─────┘
                       ▼
                  Continue Flow
```

---

# 8. End-to-End Architecture in One View

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                       │
│                                                                         │
│        "Compare the major competitors in the Indian market..."          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS FRONTEND                                │
│                                                                         │
│ Question Input ─── Live Agent Progress ─── Report Viewer ─── Export     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI                                       │
│                                                                         │
│                         Research API                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LANGGRAPH                                      │
│                                                                         │
│  ┌─────────┐    ┌───────────────────┐    ┌───────────┐                 │
│  │ Planner │───►│ Parallel Research │───►│  Checker  │                 │
│  └─────────┘    └───────────────────┘    └─────┬─────┘                 │
│                                                │                        │
│                              Weak/Conflict ────┤                        │
│                                                │                        │
│                                                ▼                        │
│                                         Research Retry                 │
│                                                │                        │
│                                                ▼                        │
│                                          ┌──────────┐                   │
│                                          │ Comparer │                   │
│                                          └────┬─────┘                   │
│                                               │                         │
│                                               ▼                         │
│                                          ┌────────┐                     │
│                                          │ Writer │                     │
│                                          └────┬───┘                     │
└──────────────────────────────────────────────┼─────────────────────────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     ▼                     ▼
                  ┌────────────┐       ┌─────────────┐       ┌────────────┐
                  │ OpenRouter │       │   Tavily    │       │  Supabase  │
                  │    LLMs    │       │   Search    │       │ PostgreSQL │
                  └────────────┘       └─────────────┘       └────────────┘
                                              
                                               │
                                               ▼
                              ┌──────────────────────────┐
                              │       FINAL REPORT       │
                              │                          │
                              │ Summary                  │
                              │ Comparison Table        │
                              │ Verified Facts           │
                              │ 🟢 🟡 🔴 Trust Tags       │
                              │ Conflicting Information  │
                              │ Research Gaps            │
                              │ Source Links             │
                              └──────────────────────────┘
                              
                              





