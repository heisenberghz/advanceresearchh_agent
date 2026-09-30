"""Unit tests for ResearchOps domain models validation and relational integrity."""

import pytest
from pydantic import ValidationError
from app.models import (
    TrustTag,
    VerificationStatus,
    JobStatus,
    RunStatus,
    ConflictStatus,
    Evidence,
    Source,
    Fact,
    VerificationResult,
    CompetingValue,
    Conflict,
    ResearchGap,
    ResearchJob,
    ComparisonCell,
    ComparisonMatrix,
    ResearchReport,
    ResearchRun,
)


def test_research_run_validation():
    """Verify ResearchRun requires valid question and defaults."""
    run = ResearchRun(id="run-1", question="Who are the main CRM competitors in India?")
    assert run.status == RunStatus.PENDING
    assert run.assumptions == []

    # Short question should be rejected
    with pytest.raises(ValidationError):
        ResearchRun(id="run-2", question="crm")


def test_source_and_evidence_validation():
    """Verify Source requires valid URL and Evidence requires non-empty text."""
    source = Source(
        id="src-1",
        research_run_id="run-1",
        url="https://techcrunch.com/2026/01/crm-india",
        title="Indian CRM Growth",
        domain="techcrunch.com",
    )
    assert source.url == "https://techcrunch.com/2026/01/crm-india"

    # Invalid URL should be rejected
    with pytest.raises(ValidationError):
        Source(id="src-2", research_run_id="run-1", url="not-a-valid-url")

    # Evidence creation
    evidence = Evidence(
        source_id="src-1",
        text="Zoho reported 30% YoY growth in Indian enterprise accounts.",
        location="Paragraph 4",
    )
    assert evidence.source_id == "src-1"

    # Empty evidence text should be rejected
    with pytest.raises(ValidationError):
        Evidence(source_id="src-1", text="   ")


def test_fact_and_verification_result():
    """Verify Fact preserves evidence, source links, and rejects invalid trust tags."""
    evidence = Evidence(source_id="src-1", text="Company founded in 1996.")
    fact = Fact(
        id="fact-1",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Founded",
        value="1996",
        source_ids=["src-1"],
        evidence=[evidence],
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
    )
    assert fact.trust_tag == TrustTag.GREEN
    assert fact.source_ids == ["src-1"]
    assert len(fact.evidence) == 1

    # Blank entity must be rejected
    with pytest.raises(ValidationError):
        Fact(id="f2", research_run_id="run-1", entity="", attribute="Revenue", value="100M")

    # Verification result model
    res = VerificationResult(
        fact_id="fact-1",
        status=VerificationStatus.VERIFIED,
        trust_tag=TrustTag.GREEN,
        reason="Corroborated across official company filing and TechCrunch report.",
        supporting_sources=["src-1"],
    )
    assert res.trust_tag == TrustTag.GREEN


def test_conflict_requires_competing_values():
    """Verify Conflict model enforces at least two competing values."""
    comp1 = CompetingValue(value="₹100 Cr", source_url="https://source-a.com", evidence="Reported ₹100 Cr revenue.")
    comp2 = CompetingValue(value="₹130 Cr", source_url="https://source-b.com", evidence="Reported ₹130 Cr revenue.")

    conflict = Conflict(
        id="conf-1",
        research_run_id="run-1",
        description="Conflicting revenue disclosures for FY25",
        competing_values=[comp1, comp2],
        supporting_sources=["src-a", "src-b"],
    )
    assert conflict.status == ConflictStatus.UNRESOLVED
    assert len(conflict.competing_values) == 2

    # Fewer than 2 competing values must be rejected
    with pytest.raises(ValidationError):
        Conflict(
            id="conf-2",
            research_run_id="run-1",
            description="Single value conflict",
            competing_values=[comp1],
        )


def test_research_gap_validation():
    """Verify ResearchGap model records missing information explicitly."""
    gap = ResearchGap(
        id="gap-1",
        research_run_id="run-1",
        requested_information="Private enterprise contract discount tiers",
        reason="Information is proprietary and strictly confidential per sales policy.",
        attempts=3,
    )
    assert gap.attempts == 3
    assert gap.status == "gap"

    # Empty reason must be rejected
    with pytest.raises(ValidationError):
        ResearchGap(id="gap-2", research_run_id="run-1", requested_information="Pricing", reason="")


def test_comparison_and_report_integration():
    """Verify ComparisonMatrix and ResearchReport composite models."""
    cell = ComparisonCell(
        entity="Zoho",
        metric="Founded",
        value="1996",
        trust_tag=TrustTag.GREEN,
        fact_id="fact-1",
        source_ids=["src-1"],
    )
    matrix = ComparisonMatrix(
        entities=["Zoho"],
        metrics=["Founded"],
        cells=[cell],
    )
    assert len(matrix.cells) == 1

    report = ResearchReport(
        id="rep-1",
        research_run_id="run-1",
        title="Indian CRM Market Competitive Analysis",
        executive_summary="Executive synthesis of Indian CRM providers.",
        comparison=matrix,
        key_findings=["Zoho leads mid-market; Salesforce dominates Tier-1 enterprise."],
    )
    assert report.id == "rep-1"
    assert report.comparison.cells[0].trust_tag == TrustTag.GREEN
