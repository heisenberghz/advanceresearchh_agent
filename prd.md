# ResearchOps — Product Requirements Document

**Project:** GATEWAYS 2026  
**Team:** Reservoir Dogs  
**Product:** ResearchOps — The Autonomous Research Agent  
**Domain:** Enterprise & Business Operations  
**Version:** 1.0

---

## 1. Product Overview

ResearchOps is an autonomous AI research system that helps users answer complex business research questions.

The user provides one natural-language business question. ResearchOps plans the research, divides it into smaller tasks, researches those tasks in parallel, verifies the collected evidence, identifies conflicting or missing information, builds comparisons where appropriate, and generates a traceable research report.

The core product principle is:

> **ResearchOps should not only provide answers. It should show the evidence behind those answers and make uncertainty visible.**

---

## 2. Problem Statement

Business research is often slow and manual.

When a company needs to make a decision—such as entering a market, choosing a supplier, or analyzing competitors—people typically have to:

1. Search multiple websites.
2. Read many pages.
3. Extract relevant facts.
4. Compare companies manually.
5. Check whether information is current.
6. Resolve conflicting information.
7. Write a report.
8. Track the sources used.

This creates several problems:

- Important information can be missed.
- Old or weak sources can be treated as reliable.
- Conflicting information can go unnoticed.
- Unsupported claims can enter reports.
- Research can take several hours.
- It can be difficult for decision-makers to verify the final result.

ResearchOps aims to reduce the time required for research while improving transparency and traceability.

---

## 3. Target Users

### Primary Users

- Business analysts
- Founders
- Managers
- Strategy teams
- Small businesses without dedicated research teams

### Example Users

A founder wants to understand competitors before entering a market.

An analyst needs to compare several suppliers.

A manager wants to research a new industry.

A small business owner needs a quick market overview without manually browsing dozens of websites.

---

## 4. Product Goal

The product should allow a user to enter a complex business question and receive a useful research report with:

- A concise summary
- Structured findings
- Comparison tables where appropriate
- Source links
- Evidence supporting important claims
- Trust indicators
- Conflicting information
- Research gaps
- Downloadable output

The user should be able to understand not only **what the system found**, but also **why the information should or should not be trusted**.

---

## 5. Core User Journey

```text
User enters business question
            ↓
Planner understands question
            ↓
Planner creates research jobs
            ↓
Research jobs execute in parallel
            ↓
Researchers collect web evidence
            ↓
Facts are extracted
            ↓
Checker verifies facts
            ↓
       ┌────┴────┐
       │         │
    Verified   Weak/Conflict
       │         │
       │      Research Again
       │         │
       │      Re-check
       └────┬────┘
            ↓
     Verified facts
            ↓
       Comparison
            ↓
         Writer
            ↓
      Final report
            ↓
       User reviews
```

---

## 6. Core Features

## 6.1 Business Question Input

The user must be able to enter a natural-language business question.

Example:

> "Who are the main competitors for our product in the Indian market, and how do they compare?"

The question should not require a predefined template.

---

## 6.2 Planning

The Planner interprets the question and converts it into structured research tasks.

The Planner should:

- Identify the main research objective.
- Identify entities that need to be researched.
- Identify important comparison dimensions.
- Detect ambiguity.
- Make reasonable assumptions when required.
- Create independent research jobs.

Example:

```text
Question:
Compare major CRM competitors in India.

Assumptions:
- Market: India
- Time period: latest available information
- Competitors: major publicly identifiable competitors

Research jobs:
1. Identify major competitors.
2. Research Company A.
3. Research Company B.
4. Research Company C.
5. Compare pricing.
6. Compare market positioning.
7. Compare company size.
```

The Planner should produce structured output rather than only natural-language instructions.

---

## 6.3 Parallel Research

Independent research jobs should execute concurrently where practical.

Each Researcher should:

1. Receive one research job.
2. Search the web.
3. Identify relevant sources.
4. Read relevant information.
5. Extract useful facts.
6. Attach source information.
7. Return structured research results.

The system should avoid making all research tasks dependent on one another unless there is a real dependency.

---

## 6.4 Evidence Collection

Important facts must be associated with supporting evidence.

A fact should conceptually contain:

- Entity
- Attribute
- Value
- Source
- Source URL
- Supporting evidence
- Publication date when available
- Retrieval date
- Verification status
- Trust tag

Example:

```text
Entity: Company A
Attribute: Founded
Value: 2012

Source: Company website
Evidence: Company A was founded in 2012.

Trust: GREEN
Status: Verified
```

---

## 6.5 Fact Verification

The Checker reviews facts produced by Researchers.

The Checker should evaluate:

- Whether a source exists.
- Whether the source actually supports the claim.
- Whether the information is sufficiently recent.
- Whether the source is reasonably authoritative.
- Whether multiple sources agree.
- Whether credible sources conflict.

The Checker must not simply accept a Researcher's claim.

---

## 6.6 Trust Tags

Every important fact should receive a visible trust indicator.

### GREEN

Strongly supported by sufficient evidence.

### YELLOW

Evidence exists but has limitations.

Possible reasons:

- Limited corroboration
- Older information
- Less authoritative source
- Some disagreement between sources

### RED

Weak, unsupported, or unresolved.

Possible reasons:

- No adequate source
- Evidence does not support the claim
- Significant unresolved conflict
- Information is too old
- Research could not verify the claim

Trust tags should be based on explicit verification rules rather than arbitrary model opinion.

---

## 6.7 Conflict Detection

ResearchOps must identify conflicting information.

Example:

```text
Metric: Revenue

Source A: ₹100 Cr
Source B: ₹130 Cr
```

The system should preserve both values and show the disagreement.

Example presentation:

```text
CONFLICT DETECTED

Source A reports: ₹100 Cr
Source B reports: ₹130 Cr

Status: Unresolved conflict
Trust: YELLOW
```

The system must not silently choose one value.

If one source appears more authoritative, the report may explain why, but the original disagreement should remain visible.

---

## 6.8 Missing Information

ResearchOps must never invent information.

If information cannot be sufficiently verified:

```text
Pricing: Not found

Reason:
No sufficiently reliable public pricing information was identified.

Status:
Research gap
```

Missing information should appear in a dedicated Research Gaps section.

---

## 6.9 Retry / Re-Research

Weak or insufficient evidence should be eligible for additional research.

Example:

```text
Research
   ↓
Checker
   ↓
Insufficient evidence
   ↓
Research again
   ↓
Checker
   ↓
Still insufficient
   ↓
Mark as gap / uncertain
```

Retries must be bounded to prevent infinite loops and excessive API usage.

---

## 6.10 Comparison

When the question requires comparing entities, the system should generate a structured comparison table.

Example:

| Metric | Company A | Company B | Company C |
|---|---|---|---|
| Founded | 2012 🟢 | 2015 🟢 | 2010 🟡 |
| Pricing | ₹X 🟢 | Not found 🔴 | ₹Y 🟢 |
| Employees | X 🟡 | Y 🟢 | Z 🟢 |

Comparison values should come from checked research data.

---

## 6.11 Final Report

The final report should contain:

### Executive Summary

A concise summary of the research findings.

### Assumptions

Assumptions made by the Planner.

### Comparison

Side-by-side comparison where applicable.

### Key Findings

Important research findings.

### Evidence

Supporting evidence and sources.

### Conflicting Information

Known disagreements between sources.

### Research Gaps

Information that could not be sufficiently verified.

### Source List

Relevant source links.

---

## 6.12 Source Traceability

Important facts must be traceable back to their sources.

The user should be able to identify:

```text
Fact
 ↓
Evidence
 ↓
Source
 ↓
Original webpage
```

The system should make source inspection straightforward.

---

## 6.13 Live Progress

The frontend should display the current research workflow.

Example:

```text
Research in progress

✓ Planner
  Created 6 research tasks

✓ Researcher 1
  Completed competitor identification

● Researcher 2
  Searching Company A pricing

● Researcher 3
  Verifying Company B revenue

○ Checker
  Waiting for research

○ Comparer
  Waiting

○ Writer
  Waiting
```

The purpose is to make the autonomous workflow visible to the user.

---

## 6.14 Changed Questions / Incremental Research

If the user changes or extends the request, existing useful research should be preserved where possible.

Example:

```text
Original:
Compare A, B and C.

Updated:
Also add D.

Planner:
A → reuse
B → reuse
C → reuse
D → research
```

Only affected research should be rerun where practical.

---

## 6.15 Report Export

The MVP should support:

- Markdown export
- PDF export

Exports should contain the important information visible in the final report.

---

# 7. Non-Functional Requirements

## Reliability

The system should prefer returning incomplete but transparent research over fabricated or unsupported information.

## Transparency

Important claims should have evidence and source information.

## Cost Control

The system should:

- Prefer lower-cost models for bulk research.
- Use stronger models only where useful.
- Avoid unnecessary repeated searches.
- Reuse existing results where possible.
- Limit research retries.

## Performance

Independent research tasks should run in parallel where practical.

## Security

API keys must remain on the backend and must never be exposed to the frontend.

## Usability

The user should understand:

- What the system is doing.
- What it found.
- What is trustworthy.
- What is uncertain.
- Where the information came from.

---

# 8. MVP Scope

## P0 — Demo Critical

- Question input
- Planner
- Research jobs
- Parallel research
- Tavily search
- Evidence extraction
- Checker
- Trust tags
- Conflict detection
- Research gaps
- Retry loop
- Comparison
- Final report

## P1 — Product Experience

- Next.js interface
- Live progress
- Source inspection
- Report viewer
- Comparison UI

## P2 — Polish

- Persistent research history
- Result caching
- Incremental research
- PDF export
- Responsive design
- Dark/light mode
- Improved error states

---

# 9. Non-Goals

The MVP does not require:

- Complex authentication
- Multi-tenant infrastructure
- Billing
- Enterprise permissions
- Custom model training
- Mobile applications
- Distributed microservices
- Complex vector databases
- Advanced long-term memory
- Large numbers of specialized agents

These should only be added if they become necessary.

---

# 10. Success Criteria

The MVP is successful when a user can:

1. Enter a realistic business research question.
2. See the question converted into research tasks.
3. See multiple research tasks execute.
4. See evidence collected from web sources.
5. See facts verified.
6. See weak evidence trigger additional research.
7. See conflicts explicitly identified.
8. See missing information marked as gaps.
9. See verified information compared.
10. Receive a final report.
11. Trace important facts to sources.
12. See trust indicators.
13. Download the report.
14. Modify a request without unnecessarily restarting all research.

---

# 11. Product Principle

ResearchOps should not behave like a chatbot that searches and summarizes.

The core product pipeline is:

```text
Question
   ↓
Plan
   ↓
Research
   ↓
Evidence
   ↓
Verification
   ↓
Conflicts + Gaps
   ↓
Comparison
   ↓
Report
   ↓
Traceable Answer
```

The evidence-verification loop is the central differentiator of the product.