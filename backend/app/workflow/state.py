"""LangGraph central workflow state definition with deterministic deduplicating reducers.

Specification: PRD.md Section 5 & TECH_SPEC.md Section 17.
Critical invariants:
- Parallel branches must never overwrite or drop facts, sources, jobs, or conflicts.
- Fact -> Source -> Evidence provenance is preserved through every merge.
- Reducers are strictly deterministic and idempotent.
"""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from app.models.comparison import ComparisonMatrix
from app.models.conflict import Conflict
from app.models.fact import Fact, VerificationResult
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.models.report import ResearchReport
from app.models.source import Source


# =====================================================================
# Deterministic State Reducer Functions
# =====================================================================

def merge_unique_strings(
    existing: Optional[List[str]],
    updates: Optional[List[str]],
) -> List[str]:
    """Merge string lists preserving first-seen order and eliminating duplicates."""
    base = list(existing or [])
    seen = set(base)
    for item in updates or []:
        if item and item not in seen:
            base.append(item)
            seen.add(item)
    return base


def reduce_jobs(
    existing: Optional[List[ResearchJob]],
    updates: Optional[List[ResearchJob]],
) -> List[ResearchJob]:
    """Merge ResearchJob records by job.id.

    If a job already exists, its state is updated (status, attempts, result_data, error).
    New jobs are appended.
    """
    job_map: Dict[str, ResearchJob] = {j.id: j for j in (existing or [])}
    for up in updates or []:
        if up.id in job_map:
            # Update mutable fields while keeping identity
            curr = job_map[up.id]
            curr.status = up.status
            curr.attempts = max(curr.attempts, up.attempts)
            curr.result_data.update(up.result_data)
            if up.error is not None:
                curr.error = up.error
            curr.updated_at = up.updated_at
        else:
            job_map[up.id] = up
    return list(job_map.values())


def reduce_facts(
    existing: Optional[List[Fact]],
    updates: Optional[List[Fact]],
) -> List[Fact]:
    """Merge Fact records by fact.id preserving evidence and source provenance.

    If a fact with the same ID arrives (e.g. from the Checker updating trust_tag),
    its verification fields are updated while preserving underlying evidence.
    New facts are appended.
    """
    fact_map: Dict[str, Fact] = {f.id: f for f in (existing or [])}
    for up in updates or []:
        if up.id in fact_map:
            curr = fact_map[up.id]
            # Update verification & trust status
            curr.verification_status = up.verification_status
            curr.trust_tag = up.trust_tag
            if up.verification_reason:
                curr.verification_reason = up.verification_reason
            # Merge sources and evidence if additional sources arrived
            for s_id in up.source_ids:
                if s_id not in curr.source_ids:
                    curr.source_ids.append(s_id)
            existing_ev_texts = {e.text for e in curr.evidence}
            for ev in up.evidence:
                if ev.text not in existing_ev_texts:
                    curr.evidence.append(ev)
                    existing_ev_texts.add(ev.text)
            curr.updated_at = up.updated_at
        else:
            fact_map[up.id] = up
    return list(fact_map.values())


def reduce_sources(
    existing: Optional[List[Source]],
    updates: Optional[List[Source]],
) -> List[Source]:
    """Merge Source records by source.id and canonical URL.

    Prevents duplicate bibliographical citations while preserving all metadata.
    """
    source_map_by_id: Dict[str, Source] = {s.id: s for s in (existing or [])}
    source_map_by_url: Dict[str, Source] = {s.url: s for s in (existing or [])}

    for up in updates or []:
        if up.id in source_map_by_id:
            # Update existing by ID
            curr = source_map_by_id[up.id]
            if up.title and not curr.title:
                curr.title = up.title
            if up.evidence and not curr.evidence:
                curr.evidence = up.evidence
        elif up.url in source_map_by_url:
            # Duplicate URL cited under a different temporary ID: merge snippets
            curr = source_map_by_url[up.url]
            if up.evidence and curr.evidence and up.evidence not in curr.evidence:
                curr.evidence = f"{curr.evidence}\n---\n{up.evidence}"
        else:
            source_map_by_id[up.id] = up
            source_map_by_url[up.url] = up

    return list(source_map_by_id.values())


def reduce_conflicts(
    existing: Optional[List[Conflict]],
    updates: Optional[List[Conflict]],
) -> List[Conflict]:
    """Merge Conflict records by conflict.id."""
    conflict_map: Dict[str, Conflict] = {c.id: c for c in (existing or [])}
    for up in updates or []:
        if up.id in conflict_map:
            curr = conflict_map[up.id]
            curr.status = up.status
            curr.description = up.description
        else:
            conflict_map[up.id] = up
    return list(conflict_map.values())


def reduce_gaps(
    existing: Optional[List[ResearchGap]],
    updates: Optional[List[ResearchGap]],
) -> List[ResearchGap]:
    """Merge ResearchGap records by gap.id."""
    gap_map: Dict[str, ResearchGap] = {g.id: g for g in (existing or [])}
    for up in updates or []:
        if up.id in gap_map:
            curr = gap_map[up.id]
            curr.attempts = max(curr.attempts, up.attempts)
            curr.reason = up.reason
        else:
            gap_map[up.id] = up
    return list(gap_map.values())


def reduce_retry_counts(
    existing: Optional[Dict[str, int]],
    updates: Optional[Dict[str, int]],
) -> Dict[str, int]:
    """Merge retry counts dictionary taking maximum count per target entity/job."""
    base = dict(existing or {})
    for k, v in (updates or {}).items():
        base[k] = max(base.get(k, 0), v)
    return base


def reduce_errors(
    existing: Optional[List[str]],
    updates: Optional[List[str]],
) -> List[str]:
    """Append new distinct error messages."""
    return merge_unique_strings(existing, updates)


# =====================================================================
# Central LangGraph Workflow State
# =====================================================================

class ResearchState(TypedDict):
    """Central state object passed between nodes in the LangGraph workflow."""

    # Run Identifiers & Scoping
    research_id: str
    question: str
    assumptions: Annotated[List[str], merge_unique_strings]
    entities: Annotated[List[str], merge_unique_strings]

    # Planning & Jobs
    research_jobs: Annotated[List[ResearchJob], reduce_jobs]
    research_results: Annotated[List[Dict[str, Any]], lambda x, y: (x or []) + (y or [])]

    # Collected Research Findings & Provenance
    facts: Annotated[List[Fact], reduce_facts]
    sources: Annotated[List[Source], reduce_sources]

    # Verification, Conflicts & Gaps
    verification_results: Annotated[List[VerificationResult], lambda x, y: (x or []) + (y or [])]
    conflicts: Annotated[List[Conflict], reduce_conflicts]
    gaps: Annotated[List[ResearchGap], reduce_gaps]

    # Comparison & Synthesis
    comparison: Optional[ComparisonMatrix]
    report: Optional[ResearchReport]

    # Operational Controls
    retry_counts: Annotated[Dict[str, int], reduce_retry_counts]
    workflow_status: str
    errors: Annotated[List[str], reduce_errors]


def create_initial_research_state(research_id: str, question: str) -> ResearchState:
    """Instantiate a pristine research state for a new business question."""
    return {
        "research_id": research_id,
        "question": question.strip(),
        "assumptions": [],
        "entities": [],
        "research_jobs": [],
        "research_results": [],
        "facts": [],
        "sources": [],
        "verification_results": [],
        "conflicts": [],
        "gaps": [],
        "comparison": None,
        "report": None,
        "retry_counts": {},
        "workflow_status": "initialized",
        "errors": [],
    }
