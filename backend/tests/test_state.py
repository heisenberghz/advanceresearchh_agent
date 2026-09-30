"""Unit tests for LangGraph ResearchState and deterministic reducers."""

import pytest
from langgraph.graph import END, START, StateGraph

from app.models.enums import ConflictStatus, JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.state import (
    ResearchState,
    create_initial_research_state,
    merge_unique_strings,
    reduce_facts,
    reduce_jobs,
    reduce_retry_counts,
    reduce_sources,
)


def test_create_initial_research_state():
    """Verify clean initialization of ResearchState."""
    state = create_initial_research_state("run-100", "Compare Indian CRM competitors")
    assert state["research_id"] == "run-100"
    assert state["question"] == "Compare Indian CRM competitors"
    assert state["workflow_status"] == "initialized"
    assert len(state["facts"]) == 0
    assert len(state["sources"]) == 0
    assert len(state["research_jobs"]) == 0
    assert state["retry_counts"] == {}


def test_reduce_facts_preserves_provenance_and_prevents_duplicates():
    """Verify reduce_facts updates existing facts without duplication and retains evidence."""
    ev1 = Evidence(source_id="src-1", text="Founded in 1996.")
    initial_fact = Fact(
        id="fact-01",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Founded",
        value="1996",
        source_ids=["src-1"],
        evidence=[ev1],
        trust_tag=TrustTag.RED,
        verification_status=VerificationStatus.UNSUPPORTED,
    )

    # 1. Append initial fact
    merged = reduce_facts([], [initial_fact])
    assert len(merged) == 1
    assert merged[0].trust_tag == TrustTag.RED

    # 2. Update same fact (e.g. from Checker with new trust_tag and additional source)
    ev2 = Evidence(source_id="src-2", text="Company registration confirmed 1996.")
    updated_fact = Fact(
        id="fact-01",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Founded",
        value="1996",
        source_ids=["src-2"],
        evidence=[ev2],
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        verification_reason="Corroborated across two authoritative sources",
    )

    merged = reduce_facts(merged, [updated_fact])

    # Invariant: No duplicate fact record created
    assert len(merged) == 1
    f = merged[0]
    assert f.trust_tag == TrustTag.GREEN
    assert f.verification_status == VerificationStatus.VERIFIED
    # Invariant: Evidence from both sources preserved
    assert len(f.evidence) == 2
    assert set(f.source_ids) == {"src-1", "src-2"}


def test_reduce_sources_deduplication():
    """Verify reduce_sources deduplicates identical URLs and IDs."""
    src1 = Source(id="s1", research_run_id="r1", url="https://zoho.com", title="Zoho")
    src2 = Source(id="s2", research_run_id="r1", url="https://zoho.com", title="Zoho Homepage")
    src3 = Source(id="s3", research_run_id="r1", url="https://salesforce.com", title="Salesforce")

    # Add src1 and src3
    res = reduce_sources([], [src1, src3])
    assert len(res) == 2

    # Add src2 with duplicate URL
    res = reduce_sources(res, [src2])
    # Should maintain 2 unique sources by URL
    assert len(res) == 2
    urls = {s.url for s in res}
    assert urls == {"https://zoho.com", "https://salesforce.com"}


def test_reduce_jobs_and_retry_counts():
    """Verify job status transitions and retry count merging."""
    job1 = ResearchJob(id="j1", research_run_id="r1", description="Task 1", status=JobStatus.PENDING)
    job2 = ResearchJob(id="j2", research_run_id="r1", description="Task 2", status=JobStatus.PENDING)

    jobs = reduce_jobs([], [job1, job2])
    assert len(jobs) == 2

    # Update job 1 to completed
    job1_updated = ResearchJob(id="j1", research_run_id="r1", description="Task 1", status=JobStatus.COMPLETED, attempts=2)
    jobs = reduce_jobs(jobs, [job1_updated])
    assert len(jobs) == 2
    j1_result = next(j for j in jobs if j.id == "j1")
    assert j1_result.status == JobStatus.COMPLETED
    assert j1_result.attempts == 2

    # Retry counts
    counts = reduce_retry_counts({"j1": 1}, {"j1": 3, "j2": 1})
    assert counts == {"j1": 3, "j2": 1}


def test_langgraph_parallel_branches_state_merging():
    """Verify LangGraph StateGraph compiles and merges parallel branch outputs without losing state."""
    # Define two parallel worker nodes
    def worker_a(state: ResearchState) -> dict:
        src_a = Source(id="src-a", research_run_id=state["research_id"], url="https://company-a.com")
        fact_a = Fact(
            id="fact-a",
            research_run_id=state["research_id"],
            entity="Company A",
            attribute="Pricing",
            value="Free tier available",
            source_ids=[src_a.id],
            evidence=[Evidence(source_id=src_a.id, text="Free tier available for 5 users.")],
        )
        return {
            "facts": [fact_a],
            "sources": [src_a],
            "retry_counts": {"job-a": 1},
        }

    def worker_b(state: ResearchState) -> dict:
        src_b = Source(id="src-b", research_run_id=state["research_id"], url="https://company-b.com")
        fact_b = Fact(
            id="fact-b",
            research_run_id=state["research_id"],
            entity="Company B",
            attribute="Pricing",
            value="Enterprise custom quote",
            source_ids=[src_b.id],
            evidence=[Evidence(source_id=src_b.id, text="Custom quote required for enterprise.")],
        )
        return {
            "facts": [fact_b],
            "sources": [src_b],
            "retry_counts": {"job-b": 1},
        }

    # Build LangGraph graph with parallel branches from START
    builder = StateGraph(ResearchState)
    builder.add_node("worker_a", worker_a)
    builder.add_node("worker_b", worker_b)

    builder.add_edge(START, "worker_a")
    builder.add_edge(START, "worker_b")
    builder.add_edge("worker_a", END)
    builder.add_edge("worker_b", END)

    graph = builder.compile()

    # Invoke graph with initial state
    initial = create_initial_research_state("run-test-graph", "Compare pricing")
    final_state = graph.invoke(initial)

    # Invariant: Neither branch dropped the other's state
    assert len(final_state["facts"]) == 2
    fact_entities = {f.entity for f in final_state["facts"]}
    assert fact_entities == {"Company A", "Company B"}

    assert len(final_state["sources"]) == 2
    assert final_state["retry_counts"] == {"job-a": 1, "job-b": 1}
