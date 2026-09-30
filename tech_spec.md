# ResearchOps — Technical Specification

**Project:** GATEWAYS 2026  
**Team:** Reservoir Dogs  
**Product:** ResearchOps — The Autonomous Research Agent  
**Version:** 1.0

---

# 1. Technical Objective

Build a reliable autonomous research pipeline that:

1. Accepts a natural-language business question.
2. Converts it into structured research tasks.
3. Executes independent research tasks concurrently.
4. Collects web evidence.
5. Extracts structured facts.
6. Independently verifies facts.
7. Detects conflicts and information gaps.
8. Performs bounded additional research when necessary.
9. Generates comparisons.
10. Produces a traceable final report.
11. Streams workflow progress to the frontend.
12. Persists research state and results.

The implementation should prioritize:

> **Reliability > Simplicity > Speed > Elegance**

Avoid unnecessary infrastructure and abstractions.

---

# 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Frontend language | TypeScript |
| Styling | Tailwind CSS |
| UI components | shadcn/ui |
| Backend | FastAPI |
| Backend language | Python |
| Agent orchestration | LangGraph |
| Web search | Tavily API |
| LLM gateway | OpenRouter |
| Research/checking model | DeepSeek or equivalent low-cost model |
| Report generation | Stronger model through OpenRouter |
| Database | Supabase PostgreSQL |
| Frontend hosting | Vercel |
| Backend hosting | Render or Railway |
| Report formats | Markdown + PDF |

---

# 3. High-Level Architecture

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │    Next.js UI   │
                  └────────┬────────┘
                           │
                     API + Streaming
                           │
                           ▼
                  ┌─────────────────┐
                  │     FastAPI     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    LangGraph    │
                  │    Workflow     │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Planner         Researchers        Checker
                           │                │
                           ▼                │
                         Tavily             │
                                            │
                              Weak evidence │
                                    ┌───────┘
                                    ▼
                              Re-research
                                    │
                                    ▼
                                Comparer
                                    │
                                    ▼
                                 Writer
                                    │
                                    ▼
                              Final Report

                    ┌─────────────────────┐
                    │      Supabase       │
                    │      PostgreSQL     │
                    └─────────────────────┘
```

---

# 4. Component Responsibilities

## 4.1 Frontend

Responsibilities:

- Accept research questions.
- Start research.
- Display research progress.
- Display research results.
- Display trust tags.
- Display conflicts.
- Display research gaps.
- Display comparisons.
- Display sources.
- Display final report.
- Trigger exports.

The frontend should not directly call Tavily or OpenRouter.

---

## 4.2 FastAPI Backend

Responsibilities:

- API endpoints.
- Request validation.
- Research run creation.
- Workflow initiation.
- Research status retrieval.
- Report retrieval.
- Export handling.
- Streaming workflow events.
- Backend error handling.

FastAPI should not contain the main agent workflow logic.

The workflow should be owned by LangGraph.

---

## 4.3 LangGraph

LangGraph should own:

- Workflow state.
- Agent transitions.
- Parallel research.
- Conditional retry logic.
- Workflow completion.
- Error states.

Initial workflow:

```text
planner
   ↓
research
   ↓
checker
   ↓
conditional_retry
   ↓
comparer
   ↓
writer
   ↓
complete
```

---

# 5. Agent Architecture

## 5.1 Planner

### Input

- User question
- Optional previous research state

### Responsibilities

- Understand question.
- Identify entities.
- Identify comparison dimensions.
- Identify ambiguity.
- Generate assumptions.
- Generate research jobs.

### Output

Structured research plan.

Conceptual structure:

```text
ResearchPlan
├── question
├── assumptions[]
├── entities[]
├── research_jobs[]
└── comparison_dimensions[]
```

---

# 6. Researcher

Researchers execute individual research jobs.

### Input

```text
ResearchJob
```

### Process

```text
Research Job
      ↓
Generate search query
      ↓
Tavily search
      ↓
Review search results
      ↓
Select relevant sources
      ↓
Extract evidence
      ↓
Create facts
```

### Output

Structured research results.

Each result should contain facts and their associated sources.

Independent research jobs should execute concurrently when possible.

---

# 7. Tavily Integration

Tavily is responsible for web search and retrieval.

The implementation should:

- Send targeted queries.
- Limit unnecessary searches.
- Capture source metadata.
- Preserve source URLs.
- Preserve relevant evidence.
- Record retrieval time.

The system should not treat search-result snippets alone as automatically sufficient evidence for important claims.

---

# 8. Fact Model

A fact is the fundamental research unit.

Conceptually:

```text
Fact
├── id
├── research_run_id
├── entity
├── attribute
├── value
├── normalized_value
├── source_ids[]
├── evidence[]
├── published_at
├── retrieved_at
├── verification_status
├── trust_tag
└── verification_reason
```

Example:

```text
Entity: Company A
Attribute: Founded
Value: 2012

Sources:
- Source 1

Evidence:
"Company A was founded in 2012."

Verification:
Verified

Trust:
GREEN
```

The exact database representation may differ, but provenance must be preserved.

---

# 9. Source Model

Conceptually:

```text
Source
├── id
├── url
├── title
├── domain
├── publisher
├── published_at
├── retrieved_at
└── content/evidence
```

A source may support multiple facts.

Avoid duplicating the same source unnecessarily.

---

# 10. Evidence Model

Evidence should preserve the relevant portion of a source used to support a fact.

Conceptually:

```text
Evidence
├── source_id
├── text
├── location/context
└── relevance
```

The goal is to allow the user or Checker to understand why the source supports the claim.

---

# 11. Checker Architecture

The Checker is logically independent from the Researcher.

### Input

- Facts
- Sources
- Evidence

### Checks

```text
1. Does a source exist?
2. Does evidence support the fact?
3. Is the source relevant?
4. Is the information sufficiently recent?
5. Is the source reasonably authoritative?
6. Do other sources agree?
7. Are there conflicts?
```

### Output

```text
VerificationResult
├── fact_id
├── status
├── trust_tag
├── reason
├── supporting_sources[]
└── conflicts[]
```

---

# 12. Verification Status

Possible statuses:

```text
verified
uncertain
conflicting
unsupported
missing
```

These statuses should remain distinct internally even if the UI simplifies them.

---

# 13. Trust Rules

Trust tags should be determined using explicit rules.

Conceptual inputs:

```text
Source availability
Evidence relevance
Source quality
Freshness
Corroboration
Conflict presence
```

The exact scoring mechanism should remain simple and deterministic.

Do not rely entirely on an LLM-generated confidence score.

Example conceptual behavior:

```text
Strong evidence + recent + corroborated
→ GREEN

Evidence exists but limited/old/conflicting
→ YELLOW

Unsupported or no sufficient evidence
→ RED
```

---

# 14. Conflict Model

Conflicts should be represented explicitly.

Conceptually:

```text
Conflict
├── id
├── research_run_id
├── fact_group
├── competing_values[]
├── supporting_sources[]
├── description
└── resolution_status
```

Example:

```text
Metric: Revenue

Value A: ₹100 Cr
Source: Source A

Value B: ₹130 Cr
Source: Source B

Status: unresolved
```

The system must never silently discard conflicting evidence.

---

# 15. Research Gaps

A research gap represents information that could not be sufficiently established.

Conceptually:

```text
ResearchGap
├── id
├── research_run_id
├── requested_information
├── reason
├── attempts
└── status
```

Example:

```text
Requested:
Company A pricing

Result:
Not found

Reason:
No sufficiently reliable public pricing information identified.
```

The Writer should include these gaps in the final report.

---

# 16. Retry Workflow

The Checker can request additional research.

Conceptual flow:

```text
Research
   ↓
Checker
   ↓
Evidence insufficient?
   │
   ├── NO → Continue
   │
   └── YES
          ↓
      Retry Research
          ↓
       Checker
          ↓
     Retry limit reached?
       /           \
     NO             YES
     │               │
     ↓               ↓
   Retry         Mark uncertain/gap
```

The retry count must be stored in workflow state.

A hard maximum must exist.

---

# 17. LangGraph State

The workflow should maintain a central state.

Conceptual state:

```text
ResearchState
├── research_id
├── question
├── assumptions[]
├── entities[]
├── research_jobs[]
├── research_results[]
├── facts[]
├── sources[]
├── verification_results[]
├── conflicts[]
├── gaps[]
├── comparison
├── report
├── retry_counts
├── workflow_status
└── errors[]
```

The state must contain enough information for each subsequent node without requiring unnecessary recomputation.

---

# 18. Research Job Model

Conceptually:

```text
ResearchJob
├── id
├── research_run_id
├── description
├── entity
├── attribute
├── status
├── attempts
├── result_ids[]
└── error
```

Statuses:

```text
pending
running
completed
needs_retry
failed
```

---

# 19. Parallel Research

Independent jobs should execute concurrently.

Example:

```text
                 Planner
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Job A        Job B        Job C
        │           │           │
     Research    Research    Research
        │           │           │
        └───────────┼───────────┘
                    ▼
                  Checker
```

Do not create separate infrastructure services for every researcher.

Use the orchestration capabilities already provided by the chosen workflow architecture.

---

# 20. Comparer

The Comparer receives verified or explicitly marked uncertain facts.

Responsibilities:

- Group facts by entity.
- Group facts by metric.
- Normalize values where necessary.
- Build comparison structures.
- Preserve fact IDs/source references.
- Avoid inventing missing values.

Conceptual output:

```text
Comparison
├── entities[]
├── metrics[]
└── cells[]
```

Each comparison cell should be traceable to its source fact.

---

# 21. Writer

The Writer receives:

- Original question
- Assumptions
- Verified facts
- Trust tags
- Conflicts
- Gaps
- Comparison

It produces the final report.

The Writer must not invent facts that are absent from the verified research state.

The Writer should distinguish:

- established findings,
- uncertain findings,
- conflicts,
- gaps.

---

# 22. Report Structure

The report should follow approximately:

```text
Research Report

1. Executive Summary

2. Research Scope & Assumptions

3. Comparison

4. Key Findings

5. Detailed Findings

6. Conflicting Information

7. Research Gaps

8. Sources
```

The exact formatting can evolve with the UI.

---

# 23. API Architecture

The initial API should remain small.

## Start Research

```text
POST /research
```

Purpose:

Create a new research run.

Input conceptually:

```text
{
  "question": "..."
}
```

Output should provide a research ID and initial status.

---

## Get Research

```text
GET /research/{id}
```

Purpose:

Return current research state/status.

---

## Stream Research

```text
GET /research/{id}/stream
```

Purpose:

Stream workflow events to the frontend.

---

## Get Report

```text
GET /research/{id}/report
```

Purpose:

Return completed report.

---

## Markdown Export

```text
GET /research/{id}/export/markdown
```

---

## PDF Export

```text
GET /research/{id}/export/pdf
```

---

# 24. Streaming Events

The backend should emit meaningful workflow events.

Conceptual events:

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

Events should contain enough metadata for the frontend to update the progress UI.

---

# 25. Database Architecture

Use Supabase PostgreSQL.

Initial conceptual tables:

```text
research_runs
research_jobs
facts
sources
conflicts
research_gaps
reports
```

---

## 25.1 research_runs

Conceptual fields:

```text
id
question
status
assumptions
created_at
updated_at
completed_at
```

---

## 25.2 research_jobs

Conceptual fields:

```text
id
research_run_id
description
entity
status
attempts
result_data
error
created_at
updated_at
```

---

## 25.3 facts

Conceptual fields:

```text
id
research_run_id
entity
attribute
value
normalized_value
verification_status
trust_tag
verification_reason
created_at
updated_at
```

---

## 25.4 sources

Conceptual fields:

```text
id
url
title
domain
publisher
published_at
retrieved_at
evidence
created_at
```

---

## 25.5 conflicts

Conceptual fields:

```text
id
research_run_id
description
status
created_at
```

---

## 25.6 research_gaps

Conceptual fields:

```text
id
research_run_id
requested_information
reason
attempts
status
created_at
```

---

## 25.7 reports

Conceptual fields:

```text
id
research_run_id
content
created_at
updated_at
```

The implementation may use relationships/JSON fields where appropriate. Avoid over-normalizing the schema for the MVP.

---

# 26. Caching / Reuse

The system should reuse existing useful research when possible.

Initial approach:

```text
New research request
        ↓
Check existing research
        ↓
Reusable result?
     /       \
   YES        NO
    │          │
 Reuse       Search
    │          │
    │        Store
    └────┬─────┘
         ↓
      Continue
```

Do not build a distributed cache.

Supabase persistence can be used for initial reuse.

---

# 27. Incremental Research

When the user modifies a request:

1. Planner analyzes the new request.
2. Existing research is compared against the new research plan.
3. Reusable completed jobs are retained.
4. New or affected jobs are executed.
5. Comparison is rebuilt.
6. Report is regenerated.

The MVP can use a simple job/entity matching strategy.

Perfect semantic diffing is not required.

---

# 28. Frontend Architecture

Conceptual structure:

```text
Next.js
│
├── Research Input
│
├── Research Progress
│
├── Findings
│
├── Comparison
│
├── Conflicts
│
├── Research Gaps
│
├── Sources
│
└── Final Report
```

The frontend should consume backend APIs/events.

It should not contain research logic.

---

# 29. Frontend Research Progress

The progress UI should show:

```text
Planner
Researchers
Checker
Retries
Comparer
Writer
```

Each research job should expose a useful human-readable status.

Example:

```text
● Searching Company A pricing
● Verifying Company B revenue
✓ Identified major competitors
```

Avoid exposing raw internal logs as the primary user experience.

---

# 30. Source UI

For each important fact, the frontend should provide access to:

- Source title
- Source domain
- Source URL
- Evidence
- Trust tag
- Verification reason when useful

The goal is quick inspection.

---

# 31. Error Handling

Failures must remain distinguishable from research results.

### Search failure

Mark the relevant job as failed or retryable.

### LLM failure

Retry within a bounded limit.

### No evidence

Mark as a research gap.

### Verification failure

Mark the relevant fact uncertain rather than treating it as verified.

### Complete workflow failure

Persist the failure status and expose a useful error message.

The system must never transform technical failures into fabricated research content.

---

# 32. Security

Requirements:

- Store secrets in environment variables.
- Never commit API keys.
- Never expose OpenRouter or Tavily keys to the frontend.
- All external API calls should originate from the backend.
- Validate API responses.
- Avoid unnecessary storage of sensitive user information.

---

# 33. Configuration

Model names, API keys, retry limits, and search limits should be configurable through environment/configuration rather than hard-coded throughout the application.

Example configuration categories:

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

Exact environment variable names may be adjusted during implementation.

---

# 34. Cost Control

The system should minimize unnecessary API usage.

Strategies:

1. Use a low-cost model for research.
2. Use the stronger model primarily for final report generation.
3. Limit searches per research job.
4. Limit retries.
5. Reuse existing research.
6. Avoid repeating identical searches.
7. Avoid sending unnecessarily large contexts to models.

Cost control should not compromise evidence quality.

---

# 35. Observability

For hackathon development, the backend should provide enough logging to diagnose:

- Research run ID
- Current workflow node
- Research job ID
- Search attempt
- Checker result
- Retry
- Error
- Completion

Logs should help developers debug the workflow without exposing secrets.

---

# 36. Testing Strategy

Testing should focus on the core pipeline.

## Unit Tests

Test:

- Trust-tag rules
- Conflict detection
- Research-job state transitions
- Retry limits
- Data validation

## Integration Tests

Test:

```text
Question
 → Planner
 → Research
 → Checker
 → Comparer
 → Writer
```

using mocked external APIs where appropriate.

## End-to-End Test

At least one realistic business question should run through the complete system.

---

# 37. Acceptance Test Scenario

Use a representative competitor-research question.

Example:

```text
"Compare the major competitors in the Indian CRM market based on
pricing, company size, founding year, and market presence."
```

Expected behavior:

```text
1. Planner identifies the research dimensions.

2. Planner creates research jobs.

3. Research jobs execute concurrently.

4. Tavily returns relevant sources.

5. Researchers produce structured facts.

6. Checker validates facts.

7. At least weak/uncertain facts are represented correctly.

8. Conflicting information is preserved.

9. Missing information becomes a gap.

10. Comparison table is generated.

11. Writer produces a final report.

12. Facts have source traceability.

13. Trust tags are visible.

14. Progress is visible in the frontend.

15. Report can be exported.
```

---

# 38. Deployment Architecture

```text
                 USERS
                   │
                   ▼
          ┌─────────────────┐
          │     Vercel      │
          │    Next.js      │
          └────────┬────────┘
                   │
                   │ HTTPS
                   ▼
          ┌─────────────────┐
          │ Render/Railway  │
          │    FastAPI      │
          └───────┬─────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   OpenRouter   Tavily   Supabase
      LLMs       Search   PostgreSQL
```

Secrets remain in deployment environment variables.

---

# 39. Architecture Constraints

The implementation should follow these constraints:

1. Do not expose secrets to the browser.
2. Do not allow the Writer to invent unsupported facts.
3. Do not silently discard conflicting evidence.
4. Do not represent missing information as a guessed value.
5. Do not allow unlimited research retries.
6. Do not make independent research tasks unnecessarily sequential.
7. Do not introduce unnecessary microservices.
8. Do not add infrastructure without a concrete requirement.
9. Keep the core workflow inspectable and debuggable.
10. Preserve source provenance throughout the pipeline.

---

# 40. Definition of Done

The technical implementation is considered MVP-complete when:

```text
[ ] Next.js application runs.
[ ] FastAPI backend runs.
[ ] Supabase connection works.
[ ] OpenRouter integration works.
[ ] Tavily integration works.
[ ] LangGraph workflow runs.
[ ] Planner produces structured research jobs.
[ ] Research jobs execute.
[ ] Independent jobs can run concurrently.
[ ] Research results contain source information.
[ ] Facts are represented structurally.
[ ] Checker verifies facts.
[ ] Trust tags are assigned using explicit rules.
[ ] Conflicts are detected.
[ ] Missing information is represented as gaps.
[ ] Retry loop is bounded.
[ ] Comparer generates structured comparisons.
[ ] Writer produces the final report.
[ ] Source traceability is preserved.
[ ] Frontend displays live progress.
[ ] Final report is displayed.
[ ] Markdown export works.
[ ] PDF export works.
[ ] Basic error handling works.
[ ] At least one complete end-to-end scenario works reliably.
```

---

# 41. Implementation Philosophy

ResearchOps should be implemented as a **small, reliable evidence pipeline**, not as a collection of unnecessarily complex autonomous agents.

The architecture should remain:

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

The most important technical property is that **evidence and provenance survive every stage of the workflow**.

The final report must be generated from the research state rather than from an unverified conversational summary.