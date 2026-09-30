# ResearchOps — Coding Agent Task Plan

**Project:** GATEWAYS 2026  
**Team:** Reservoir Dogs  
**Product:** ResearchOps — The Autonomous Research Agent

---

# 0. Instructions for the Coding Agent

Before implementing anything:

1. Read `PRD.md`.
2. Read `TECH_SPEC.md`.
3. Treat both documents as the source of truth for implementation.
4. Inspect the existing repository before creating or modifying files.
5. Do not introduce unnecessary frameworks, services, dependencies, or abstractions.
6. Prefer simple, reliable implementations suitable for a hackathon MVP.
7. Keep frontend and backend responsibilities clearly separated.
8. Never expose API keys or secrets to the frontend.
9. Preserve research evidence and source provenance throughout the workflow.
10. Never fabricate missing research information.
11. Never silently discard conflicting information.
12. Keep retry loops bounded.
13. Do not mark a feature complete until its acceptance criteria are satisfied.
14. After every task, report:
    - What changed
    - Files created/modified
    - What works
    - What was tested
    - What remains
    - Known issues

### Important

Do not implement all tasks at once unless explicitly instructed.

Work incrementally.

Complete one task, verify it, and wait for the next task.

---

# 1. Implementation Strategy

Build in this order:

```text
Phase 1
Project Foundation
        ↓
Phase 2
Database
        ↓
Phase 3
LLM + Search Integrations
        ↓
Phase 4
LangGraph Research Workflow
        ↓
Phase 5
Verification System
        ↓
Phase 6
Comparison + Report
        ↓
Phase 7
FastAPI
        ↓
Phase 8
Frontend
        ↓
Phase 9
Live Progress
        ↓
Phase 10
Exports + Persistence
        ↓
Phase 11
Testing + Demo Hardening
```

The backend research pipeline should be proven before spending significant time on UI polish.

---

# PHASE 1 — PROJECT FOUNDATION

## TASK 1 — Inspect Repository and Establish Structure

### Objective

Understand the existing repository and establish a clean project structure without unnecessary changes.

### Requirements

Inspect:

- Existing files
- Existing framework setup
- Package managers
- Environment configuration
- Existing frontend/backend code
- Existing dependencies

Determine whether the repository already contains:

- Next.js
- Python/FastAPI
- Supabase configuration
- Environment files
- Documentation

Do not overwrite useful existing work.

### Expected Structure

A reasonable target structure is:

```text
researchops/
├── frontend/
├── backend/
├── PRD.md
├── TECH_SPEC.md
├── AGENT_TASKS.md
└── README.md
```

The exact structure may differ if the repository already has an established organization.

### Acceptance Criteria

- Repository has been inspected.
- Existing technology choices are preserved.
- Frontend/backend boundaries are clear.
- Development commands are documented.
- No unnecessary dependencies are introduced.

---

# TASK 2 — Backend Foundation

### Objective

Create the minimal FastAPI backend foundation.

### Requirements

Implement:

- FastAPI application
- Configuration/environment loading
- Health endpoint
- Basic error handling
- Clean application structure

Create configuration support for:

```text
OPENROUTER_API_KEY
TAVILY_API_KEY
SUPABASE_URL
SUPABASE_KEY
RESEARCH_MODEL
WRITER_MODEL
MAX_RESEARCH_RETRIES
MAX_SEARCHES_PER_JOB
```

Do not hard-code secrets.

### Acceptance Criteria

- Backend starts successfully.
- Health endpoint responds.
- Missing required configuration produces a clear error.
- Secrets are not exposed.
- No unnecessary service layer complexity is introduced.

---

# TASK 3 — Frontend Foundation

### Objective

Create the minimal Next.js frontend foundation.

### Requirements

Set up:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Basic application layout

Create an initial landing/research screen containing:

- ResearchOps branding
- Question input
- Start Research button

Do not build the full dashboard yet.

### Acceptance Criteria

- Frontend starts successfully.
- UI is responsive.
- Question can be entered.
- Start button exists.
- No backend research logic is implemented in the frontend.

---

# PHASE 2 — DATABASE

# TASK 4 — Supabase Database Foundation

### Objective

Create persistence for research runs and workflow state.

### Requirements

Implement the minimum database structure needed for:

- research runs
- research jobs
- facts
- sources
- conflicts
- research gaps
- reports

Follow the conceptual schema in `TECH_SPEC.md`.

Avoid unnecessary normalization.

### Acceptance Criteria

- Database schema exists.
- Backend can connect to Supabase.
- A research run can be persisted.
- Database errors are handled clearly.

---

# TASK 5 — Research Data Models

### Objective

Create backend models/types for the research domain.

### Required conceptual models

```text
ResearchRun
ResearchJob
Fact
Source
Evidence
VerificationResult
Conflict
ResearchGap
Comparison
Report
```

Models should support validation.

Important relationships must be preserved.

### Acceptance Criteria

- Models can represent the complete research pipeline.
- Facts can reference sources.
- Conflicts can reference competing evidence.
- Research gaps can be persisted.
- Invalid data is rejected.

---

# PHASE 3 — EXTERNAL INTEGRATIONS

# TASK 6 — OpenRouter Integration

### Objective

Create a small reusable backend integration for LLM calls through OpenRouter.

### Requirements

Support:

- Research model
- Writer model
- Configurable model names
- Structured output where practical
- Basic error handling
- Timeout handling

Do not create an unnecessary abstraction layer.

### Acceptance Criteria

- Backend can successfully make an OpenRouter request.
- Model is configurable.
- API key remains server-side.
- Errors are handled.
- A simple integration test/mock exists where practical.

---

# TASK 7 — Tavily Integration

### Objective

Create the web search integration.

### Requirements

Support:

- Search query
- Configurable result limits
- Source URL
- Source title
- Domain
- Relevant content/snippet
- Publication date when available
- Retrieval timestamp

The integration should return normalized source data.

### Acceptance Criteria

- Tavily search works.
- Search results are normalized.
- Source URLs are preserved.
- API failures are handled.
- Search limits can be configured.

---

# PHASE 4 — CORE RESEARCH WORKFLOW

# TASK 8 — Planner

### Objective

Implement the Planner as the first LangGraph workflow component.

### Input

Natural-language research question.

### Output

Structured research plan containing:

```text
question
assumptions
entities
research_jobs
comparison_dimensions
```

### Requirements

The Planner should:

- Understand the question.
- Detect missing context.
- Make reasonable assumptions.
- Break the question into researchable jobs.
- Avoid generating redundant jobs.

### Acceptance Criteria

Given a realistic business question:

> "Compare the major competitors in the Indian CRM market."

the Planner produces multiple structured research jobs.

---

# TASK 9 — Researcher

### Objective

Implement the Researcher workflow component.

### Input

One research job.

### Process

```text
Research Job
     ↓
Generate search query
     ↓
Tavily
     ↓
Review results
     ↓
Extract evidence
     ↓
Create structured facts
```

### Requirements

Each fact must retain:

- Entity
- Attribute
- Value
- Evidence
- Source
- Source URL
- Retrieval date

The Researcher must not invent values when evidence is absent.

### Acceptance Criteria

A research job produces structured facts with source provenance.

---

# TASK 10 — Parallel Research

### Objective

Run independent research jobs concurrently.

### Requirements

Given:

```text
Job A
Job B
Job C
Job D
```

the workflow should execute independent jobs concurrently where practical.

Do not unnecessarily execute:

```text
A → B → C → D
```

if the jobs are independent.

### Acceptance Criteria

- Multiple research jobs can run in parallel.
- Each job maintains its own status.
- One job's failure does not automatically destroy successful results from other jobs.
- Results are merged into the workflow state.

---

# TASK 11 — LangGraph State

### Objective

Create the central research workflow state.

### State should support

```text
research_id
question
assumptions
entities
research_jobs
research_results
facts
sources
verification_results
conflicts
gaps
comparison
report
retry_counts
workflow_status
errors
```

### Acceptance Criteria

- All workflow nodes can read/write required state.
- State survives transitions.
- Research results are not lost between nodes.
- Retry counts are preserved.

---

# TASK 12 — End-to-End Research Workflow

### Objective

Connect Planner and Researchers.

### Workflow

```text
Planner
   ↓
Research Jobs
   ↓
Parallel Researchers
   ↓
Collected Facts
```

### Acceptance Criteria

A business question can run through:

```text
Question
 → Planner
 → Research
```

and return structured research data.

Do not implement Checker/Comparer/Writer yet.

---

# PHASE 5 — VERIFICATION

# TASK 13 — Checker

### Objective

Implement the independent fact verification component.

### Requirements

For each fact evaluate:

- Source existence
- Evidence relevance
- Freshness
- Source quality
- Corroboration
- Conflicts

### Output

```text
verification_status
trust_tag
verification_reason
supporting_sources
conflicts
```

### Acceptance Criteria

Checker does not blindly accept Researcher output.

A fact with insufficient evidence is marked accordingly.

---

# TASK 14 — Deterministic Trust Rules

### Objective

Implement explicit trust-tag rules.

### Rules

Trust classification should consider:

- Evidence presence
- Evidence relevance
- Source quality
- Freshness
- Corroboration
- Conflict

Conceptual behavior:

```text
Strong evidence + strong/recent sources + corroboration
→ GREEN

Evidence exists but limitations exist
→ YELLOW

Unsupported / missing / unresolved severe conflict
→ RED
```

The exact thresholds should be simple and configurable.

### Acceptance Criteria

- Trust tags are deterministic.
- Same verification inputs produce the same classification.
- LLM prose does not directly determine the final trust tag.
- Reason for classification is stored.

---

# TASK 15 — Conflict Detection

### Objective

Detect conflicting information about the same fact.

### Example

```text
Revenue

Source A → ₹100 Cr
Source B → ₹130 Cr
```

### Requirements

- Preserve both values.
- Link both sources.
- Create conflict record.
- Mark the fact appropriately.
- Do not silently choose one.

### Acceptance Criteria

Conflicting values are visible in workflow state and can reach the final report.

---

# TASK 16 — Research Retry Loop

### Objective

Allow weak research to trigger additional research.

### Workflow

```text
Research
   ↓
Checker
   ↓
Insufficient evidence?
   ↓
Retry Research
   ↓
Checker
```

### Requirements

- Retry count stored.
- Hard retry limit.
- Retry only affected jobs/facts where practical.
- After maximum retries, mark information uncertain/gap.

### Acceptance Criteria

- Retry works.
- Infinite loops are impossible.
- Search/LLM usage remains bounded.
- Failed research does not erase successful research.

---

# TASK 17 — Missing Information / Research Gaps

### Objective

Represent missing information explicitly.

### Requirements

If sufficient evidence cannot be found after allowed research attempts:

```text
Status: Research gap

Requested:
Pricing

Reason:
No sufficiently reliable public information found.
```

### Acceptance Criteria

- No fabricated value is created.
- Gap is persisted.
- Gap reaches final report.

---

# PHASE 6 — COMPARISON AND REPORTING

# TASK 18 — Comparer

### Objective

Create structured comparisons from verified research.

### Requirements

- Group facts by entity.
- Group facts by metric.
- Preserve fact/source references.
- Represent missing values clearly.
- Preserve trust tags.
- Do not invent values.

### Acceptance Criteria

Given multiple researched companies, the Comparer produces a structured comparison table.

---

# TASK 19 — Writer

### Objective

Generate the final research report.

### Input

```text
Question
Assumptions
Verified facts
Trust tags
Conflicts
Research gaps
Comparison
Sources
```

### Requirements

Report must contain:

1. Executive Summary
2. Assumptions
3. Comparison
4. Key Findings
5. Detailed Findings
6. Conflicting Information
7. Research Gaps
8. Sources

The Writer must only use information available in the research state.

### Acceptance Criteria

- Report is coherent.
- Unsupported claims are not introduced.
- Sources are preserved.
- Conflicts are visible.
- Gaps are visible.

---

# TASK 20 — Complete LangGraph Workflow

### Objective

Connect all major workflow components.

### Final workflow

```text
Planner
   ↓
Parallel Research
   ↓
Checker
   ↓
Conditional Retry
   ↓
Comparer
   ↓
Writer
   ↓
Complete
```

### Acceptance Criteria

A realistic business question can run through the complete backend workflow and produce a final report.

This is the first major MVP milestone.

---

# PHASE 7 — API

# TASK 21 — Start Research API

### Objective

Expose research execution through FastAPI.

### Endpoint

```text
POST /research
```

### Requirements

- Accept natural-language question.
- Create research run.
- Start workflow.
- Return research ID.
- Return initial status.

### Acceptance Criteria

Frontend or API client can start a research run.

---

# TASK 22 — Research Status API

### Endpoint

```text
GET /research/{id}
```

### Requirements

Return:

- Research status
- Current workflow stage
- Research jobs
- Findings where available
- Conflicts
- Gaps

### Acceptance Criteria

A client can inspect an active or completed research run.

---

# TASK 23 — Report API

### Endpoint

```text
GET /research/{id}/report
```

### Requirements

Return final report data after completion.

### Acceptance Criteria

Completed report can be retrieved independently of workflow execution.

---

# PHASE 8 — FRONTEND

# TASK 24 — Research Input UI

### Objective

Connect the existing input screen to the backend.

### Requirements

User can:

1. Enter question.
2. Click Start Research.
3. Receive research ID.
4. Navigate to research progress.

### Acceptance Criteria

A real research run can be started from the UI.

---

# TASK 25 — Research Progress Dashboard

### Objective

Build the main research-progress interface.

### Display

```text
Planner
Researchers
Checker
Retries
Comparer
Writer
```

Show statuses such as:

```text
Waiting
Running
Completed
Failed
Retrying
```

### Acceptance Criteria

The user can understand what ResearchOps is doing.

---

# TASK 26 — Findings UI

### Objective

Display researched facts.

Each fact should show:

- Entity
- Attribute
- Value
- Trust tag
- Source
- Evidence where useful

### Acceptance Criteria

Users can inspect the evidence behind important facts.

---

# TASK 27 — Comparison UI

### Objective

Display the comparison generated by the Comparer.

### Requirements

- Clear table.
- Trust indicators.
- Missing values.
- Source access.

### Acceptance Criteria

Comparison is readable and traceable.

---

# TASK 28 — Conflicts UI

### Objective

Display conflicting information prominently.

Example:

```text
⚠ Conflict detected

Revenue

Source A: ₹100 Cr
Source B: ₹130 Cr

Status: Unresolved
```

### Acceptance Criteria

Conflicts are impossible to miss in the report interface.

---

# TASK 29 — Research Gaps UI

### Objective

Display information the system could not verify.

### Acceptance Criteria

Users can clearly distinguish:

```text
Known fact
vs
Uncertain fact
vs
Missing information
```

---

# TASK 30 — Sources UI

### Objective

Make research traceable.

### Requirements

Display:

- Source title
- Domain
- URL
- Evidence
- Related fact

### Acceptance Criteria

A user can move from an important fact to its source.

---

# PHASE 9 — LIVE STREAMING

# TASK 31 — Backend Workflow Events

### Objective

Generate structured workflow events.

### Events

```text
research_started

planner_started
planner_completed

research_job_started
research_job_completed

checker_started
fact_verified
fact_marked_uncertain
conflict_detected

retry_started
retry_completed

comparer_started
comparer_completed

writer_started
writer_completed

research_completed
research_failed
```

### Acceptance Criteria

Events accurately reflect actual workflow state.

---

# TASK 32 — Frontend Live Updates

### Objective

Connect workflow events to the frontend.

### Requirements

The UI should update without manual refresh.

Example:

```text
✓ Planner
● Researcher 1
● Researcher 2
○ Checker
○ Comparer
○ Writer
```

### Acceptance Criteria

Progress updates visibly while research is running.

---

# PHASE 10 — EXPORT AND PERSISTENCE

# TASK 33 — Markdown Export

### Endpoint

```text
GET /research/{id}/export/markdown
```

### Requirements

Export:

- Summary
- Assumptions
- Comparison
- Findings
- Trust status
- Conflicts
- Gaps
- Sources

### Acceptance Criteria

Valid Markdown file is generated.

---

# TASK 34 — PDF Export

### Endpoint

```text
GET /research/{id}/export/pdf
```

### Requirements

Generate a readable PDF containing the final report.

### Acceptance Criteria

- PDF downloads successfully.
- Formatting is readable.
- Sources and trust information are retained.

---

# TASK 35 — Research History

### Objective

Allow previous research runs to be reopened.

### Requirements

Store completed research runs in Supabase.

The UI should eventually allow users to access previous reports.

### Acceptance Criteria

A completed report can be reopened after the original workflow finishes.

---

# TASK 36 — Result Reuse / Caching

### Objective

Reduce unnecessary repeated searches.

### Requirements

Before performing expensive duplicate research:

1. Check stored results.
2. Determine whether useful information exists.
3. Reuse where appropriate.
4. Search again when information is stale or insufficient.

Keep the implementation simple.

### Acceptance Criteria

Repeated compatible research can reuse existing information.

---

# PHASE 11 — INCREMENTAL RESEARCH

# TASK 37 — Changed Question Handling

### Objective

Allow additional research without restarting everything.

### Example

Original:

```text
Compare A, B and C.
```

Updated:

```text
Also include D.
```

Expected behavior:

```text
A → reuse
B → reuse
C → reuse
D → research
```

### Acceptance Criteria

The system identifies at least obvious reusable completed research and avoids unnecessary reruns.

Perfect semantic diffing is not required for the MVP.

---

# PHASE 12 — TESTING

# TASK 38 — Unit Tests

Test:

- Trust rules
- Conflict detection
- Retry limits
- Data validation
- Research job state transitions
- Missing-data handling

### Acceptance Criteria

Core deterministic logic has automated tests.

---

# TASK 39 — Integration Tests

Test:

```text
Planner
 ↓
Research
 ↓
Checker
 ↓
Comparer
 ↓
Writer
```

Mock external APIs where appropriate.

### Acceptance Criteria

The core workflow can be tested without depending entirely on live external APIs.

---

# TASK 40 — End-to-End Test

Use a realistic question:

```text
Compare the major competitors in the Indian CRM market
based on pricing, company size, founding year, and market presence.
```

Verify:

- Planner
- Parallel research
- Evidence
- Checker
- Trust tags
- Conflicts
- Gaps
- Comparison
- Writer
- API
- Frontend
- Streaming
- Export

### Acceptance Criteria

The complete product works from question input to downloadable report.

---

# PHASE 13 — DEMO HARDENING

# TASK 41 — Demo Scenario

Prepare one highly reliable demonstration scenario.

The scenario should demonstrate:

1. Complex business question.
2. Planning.
3. Parallel research.
4. Evidence collection.
5. Verification.
6. Trust tags.
7. Conflict detection.
8. Research gaps.
9. Comparison.
10. Final report.
11. Source traceability.
12. Live progress.

The demo should use a question that reliably produces enough public information.

---

# TASK 42 — Error-State Hardening

Verify behavior for:

- Tavily failure
- OpenRouter failure
- Empty search results
- Invalid LLM output
- Research timeout
- Failed research job
- Checker failure
- Report-generation failure

The application should show understandable errors rather than crashing or producing misleading output.

---

# TASK 43 — UI Polish

Only after the workflow is reliable.

Polish:

- Typography
- Spacing
- Cards
- Status indicators
- Trust badges
- Tables
- Source display
- Loading states
- Empty states
- Error states
- Dark/light mode
- Responsive behavior

Do not spend excessive time on animations or visual effects.

---

# TASK 44 — Final Reliability Pass

Verify:

```text
[ ] No secrets committed
[ ] Backend starts cleanly
[ ] Frontend starts cleanly
[ ] Database works
[ ] Tavily works
[ ] OpenRouter works
[ ] LangGraph works
[ ] Parallel research works
[ ] Checker works
[ ] Retry is bounded
[ ] Trust tags are deterministic
[ ] Conflicts are preserved
[ ] Gaps are preserved
[ ] Writer does not fabricate
[ ] Sources are traceable
[ ] Live progress works
[ ] Markdown export works
[ ] PDF export works
[ ] Demo scenario works repeatedly
```

---

# 14. Priority Rules

If time becomes limited, use this priority order.

## Must Ship

```text
1. Planner
2. Research
3. Evidence
4. Checker
5. Trust tags
6. Conflict handling
7. Research gaps
8. Final report
9. Source traceability
10. Basic frontend
```

## Should Ship

```text
11. Parallel research
12. Live progress
13. Comparison UI
14. Retry loop
15. Markdown export
16. PDF export
```

## Nice to Have

```text
17. Caching
18. Research history
19. Incremental research
20. Advanced UI polish
```

---

# 15. Features to Cut First

If the hackathon deadline becomes tight, cut in this order:

```text
Advanced animations
        ↓
Advanced settings
        ↓
Complex research history
        ↓
Sophisticated incremental diffing
        ↓
Advanced caching
        ↓
Non-essential UI polish
```

Do NOT cut:

```text
Evidence
Checker
Trust tags
Conflicts
Research gaps
Source traceability
```

These are central to the product's differentiation.

---

# 16. Coding Agent Reporting Format

After completing each task, report:

```text
## Task Completed

### What Changed
- ...

### Files Created
- ...

### Files Modified
- ...

### What Works
- ...

### Tests Run
- ...

### Test Results
- ...

### Known Issues
- ...

### Remaining Work
- ...

### Suggested Next Task
- ...
```

Do not claim a task is complete if the acceptance criteria have not been verified.

---

# 17. Final Architecture Check

Before declaring the MVP complete, verify that the implementation still follows:

```text
User Question
      ↓
Planner
      ↓
Parallel Researchers
      ↓
Evidence
      ↓
Checker
      ↓
 ┌────┴───────────────┐
 │                    │
Verified          Weak/Conflict
 │                    │
 │               Re-research
 │                    │
 └─────────┬──────────┘
           ↓
      Verified State
           ↓
        Comparer
           ↓
         Writer
           ↓
    Traceable Report
```

The implementation should preserve the central ResearchOps principle:

> **Search results are not automatically truth. Evidence must be checked before it becomes a reported finding.**

---

# 18. Final MVP Definition

The MVP is ready for the hackathon demo when:

```text
A user can enter a business question
            ↓
ResearchOps creates a plan
            ↓
Research jobs execute in parallel
            ↓
Web evidence is collected
            ↓
Facts are independently checked
            ↓
Weak evidence is retried within a limit
            ↓
Conflicts are explicitly shown
            ↓
Missing information is explicitly shown
            ↓
Verified information is compared
            ↓
A final report is generated
            ↓
Every important finding is traceable
            ↓
The user can watch the workflow live
            ↓
The report can be exported
```

This is the minimum complete ResearchOps experience.