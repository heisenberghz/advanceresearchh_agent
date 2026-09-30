"""Unit tests for the independent Checker verification component (Task 13)."""

from datetime import datetime, timezone
import pytest

from app.models.enums import ConflictStatus, TrustTag, VerificationStatus
from app.models.fact import Fact, VerificationResult
from app.models.source import Evidence, Source
from app.workflow.checker import Checker, get_checker
from app.workflow.state import reduce_verification_results


def test_checker_rejects_fact_with_missing_source():
    """Checker must mark facts with missing or nonexistent sources as UNSUPPORTED and RED."""
    checker = get_checker()

    fact = Fact(
        id="fact-1",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        source_ids=["src-nonexistent"],
        evidence=[Evidence(source_id="src-nonexistent", text="Zoho CRM costs ₹1,200/user/mo.")],
    )

    # Empty sources dictionary
    result: VerificationResult = checker.verify_fact(fact, sources_map={})

    assert result.status == VerificationStatus.UNSUPPORTED
    assert result.trust_tag == TrustTag.RED
    assert "missing or not found" in result.reason
    assert result.supporting_sources == []


def test_checker_rejects_fact_with_ungrounded_evidence():
    """Checker must reject facts where the evidence snippet does not contain the claimed value."""
    checker = get_checker()

    source = Source(
        id="src-1",
        research_run_id="run-test",
        url="https://techblog.com/zoho-review",
        title="Zoho Review",
        domain="techblog.com",
    )

    # The evidence mentions Chennai and SaaS, but does NOT contain "1980"
    fact = Fact(
        id="fact-2",
        research_run_id="run-test",
        entity="Freshworks",
        attribute="Founded",
        value="1980",
        source_ids=["src-1"],
        evidence=[Evidence(source_id="src-1", text="Freshworks was established in Chennai as a SaaS company.")],
    )

    result: VerificationResult = checker.verify_fact(fact, sources_map={"src-1": source})

    assert result.status == VerificationStatus.UNSUPPORTED
    assert result.trust_tag == TrustTag.RED
    assert "not found in evidence" in result.reason or "does not substantiate" in result.reason or "Claimed numeric" in result.reason


def test_checker_verifies_official_primary_domain_as_green():
    """Checker must verify facts directly supported by the entity's official domain with GREEN trust tag."""
    checker = get_checker()

    source = Source(
        id="src-zoho",
        research_run_id="run-test",
        url="https://www.zoho.com/crm/pricing.html",
        title="Zoho CRM Official Pricing",
        domain="zoho.com",
    )

    fact = Fact(
        id="fact-3",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        source_ids=["src-zoho"],
        evidence=[Evidence(source_id="src-zoho", text="Standard plan starts at ₹1,200/user/mo billed annually.")],
    )

    result: VerificationResult = checker.verify_fact(fact, sources_map={"src-zoho": source})

    assert result.status == VerificationStatus.VERIFIED
    assert result.trust_tag == TrustTag.GREEN
    assert "official primary source" in result.reason
    assert "zoho.com" in result.reason
    assert result.supporting_sources == ["src-zoho"]


def test_checker_verifies_corroborated_multi_source_as_green():
    """Facts corroborated by multiple independent authoritative domains should receive GREEN."""
    checker = get_checker()

    src1 = Source(
        id="src-tc",
        research_run_id="run-test",
        url="https://techcrunch.com/2023/05/10/crm-salesforce-pricing",
        title="Salesforce Enterprise Review",
        domain="techcrunch.com",
    )
    src2 = Source(
        id="src-reuters",
        research_run_id="run-test",
        url="https://reuters.com/technology/crm-market-pricing-update",
        title="CRM Market Trends",
        domain="reuters.com",
    )

    fact = Fact(
        id="fact-4",
        research_run_id="run-test",
        entity="Salesforce",
        attribute="Enterprise Pricing",
        value="$165/user/mo",
        source_ids=["src-tc", "src-reuters"],
        evidence=[
            Evidence(source_id="src-tc", text="Salesforce Enterprise edition is priced at $165/user/mo."),
            Evidence(source_id="src-reuters", text="Enterprise licenses remain steady at $165/user/mo across regions."),
        ],
    )

    sources_map = {"src-tc": src1, "src-reuters": src2}
    result: VerificationResult = checker.verify_fact(fact, sources_map=sources_map)

    assert result.status == VerificationStatus.VERIFIED
    assert result.trust_tag == TrustTag.GREEN
    assert "Corroborated across 2 independent sources" in result.reason
    assert set(result.supporting_sources) == {"src-tc", "src-reuters"}


def test_checker_marks_single_secondary_source_as_yellow():
    """Grounded fact with only a single non-primary secondary source should be tagged YELLOW (Uncertain)."""
    checker = get_checker()

    src = Source(
        id="src-blog",
        research_run_id="run-test",
        url="https://randomcloudblogger.net/crm-overview",
        title="Cloud CRM Overview",
        domain="randomcloudblogger.net",
    )

    fact = Fact(
        id="fact-5",
        research_run_id="run-test",
        entity="LeadSquared",
        attribute="Market Share",
        value="12%",
        source_ids=["src-blog"],
        evidence=[Evidence(source_id="src-blog", text="LeadSquared captured approximately 12% in the banking niche.")],
    )

    result: VerificationResult = checker.verify_fact(fact, sources_map={"src-blog": src})

    assert result.status == VerificationStatus.UNCERTAIN
    assert result.trust_tag == TrustTag.YELLOW
    assert "Single secondary source citation" in result.reason
    assert result.supporting_sources == ["src-blog"]


def test_checker_detects_and_preserves_conflicts():
    """Conflicting claims for the same entity and attribute must be flagged and preserved into Conflict models."""
    checker = get_checker()

    src1 = Source(
        id="src-zoho-1",
        research_run_id="run-test",
        url="https://zoho.com/pricing",
        title="Zoho Pricing 2024",
        domain="zoho.com",
    )
    src2 = Source(
        id="src-analyst-2",
        research_run_id="run-test",
        url="https://crmanalysts.com/zoho-costs",
        title="CRM Cost Breakdown",
        domain="crmanalysts.com",
    )

    fact1 = Fact(
        id="fact-price-1",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        source_ids=["src-zoho-1"],
        evidence=[Evidence(source_id="src-zoho-1", text="Entry pricing is ₹1,200/user/mo for Standard.")],
    )
    fact2 = Fact(
        id="fact-price-2",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹3,500/user/mo",
        source_ids=["src-analyst-2"],
        evidence=[Evidence(source_id="src-analyst-2", text="Zoho Ultimate CRM package lists at ₹3,500/user/mo.")],
    )

    batch_result = checker.check_all(
        facts=[fact1, fact2],
        sources=[src1, src2],
        research_run_id="run-test",
    )

    # 1. Conflicts detected and preserved
    assert len(batch_result.conflicts) == 1
    conflict = batch_result.conflicts[0]
    assert conflict.status == ConflictStatus.UNRESOLVED
    assert len(conflict.competing_values) == 2
    competing_vals = {cv.value for cv in conflict.competing_values}
    assert competing_vals == {"₹1,200/user/mo", "₹3,500/user/mo"}
    assert set(conflict.supporting_sources) == {"src-zoho-1", "src-analyst-2"}

    # 2. Both facts marked CONFLICTING
    for fact in batch_result.facts:
        assert fact.verification_status == VerificationStatus.CONFLICTING
        assert fact.trust_tag == TrustTag.YELLOW
        assert "Conflicting claims detected" in fact.verification_reason

    # 3. Verification results retain conflict linkage
    for v_res in batch_result.verification_results:
        assert v_res.status == VerificationStatus.CONFLICTING
        assert conflict.id in v_res.conflicts


def test_checker_batch_updates_facts_in_place_preserving_provenance():
    """Batch verification updates fact verification fields while leaving original evidence intact."""
    checker = get_checker()

    src = Source(
        id="src-fresh",
        research_run_id="run-test",
        url="https://freshworks.com/about",
        title="About Freshworks",
        domain="freshworks.com",
    )
    fact = Fact(
        id="fact-fresh-1",
        research_run_id="run-test",
        entity="Freshworks",
        attribute="Founded",
        value="2010",
        source_ids=["src-fresh"],
        evidence=[Evidence(source_id="src-fresh", text="Freshworks was founded in 2010 in Chennai.")],
    )

    batch = checker.check_all([fact], [src])
    assert len(batch.facts) == 1
    updated_fact = batch.facts[0]

    assert updated_fact.verification_status == VerificationStatus.VERIFIED
    assert updated_fact.trust_tag == TrustTag.GREEN
    assert updated_fact.evidence[0].text == "Freshworks was founded in 2010 in Chennai."
    assert updated_fact.source_ids == ["src-fresh"]
    assert updated_fact.verification_reason is not None


def test_reduce_verification_results_deduplication():
    """State reducer for verification results replaces previous results for the same fact."""
    initial = [
        VerificationResult(
            fact_id="f1",
            status=VerificationStatus.UNCERTAIN,
            trust_tag=TrustTag.YELLOW,
            reason="Initial check",
        )
    ]
    updates = [
        VerificationResult(
            fact_id="f1",
            status=VerificationStatus.VERIFIED,
            trust_tag=TrustTag.GREEN,
            reason="Corroborated after retry",
        ),
        VerificationResult(
            fact_id="f2",
            status=VerificationStatus.UNSUPPORTED,
            trust_tag=TrustTag.RED,
            reason="No source",
        ),
    ]

    merged = reduce_verification_results(initial, updates)
    assert len(merged) == 2
    f1_res = next(r for r in merged if r.fact_id == "f1")
    assert f1_res.status == VerificationStatus.VERIFIED
    assert f1_res.trust_tag == TrustTag.GREEN
    assert f1_res.reason == "Corroborated after retry"
