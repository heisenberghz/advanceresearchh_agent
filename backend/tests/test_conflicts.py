"""Unit tests for Conflict Detection & Resolution engine (Task 15)."""

from datetime import datetime, timezone
import pytest

from app.models.enums import ConflictStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.source import Evidence, Source
from app.workflow.checker import Checker, get_checker
from app.workflow.conflicts import ConflictDetector, ConflictType, get_conflict_detector
from app.workflow.state import reduce_conflicts


def test_conflict_detection_numeric_revenue_discrepancy():
    """Conflicting quantitative claims (e.g. ₹100 Cr vs ₹130 Cr) must be preserved in Conflict records."""
    detector = get_conflict_detector()

    s1 = Source(id="s1", research_run_id="run-1", url="https://news.com/zoho-rev", title="Zoho Rev")
    s2 = Source(id="s2", research_run_id="run-1", url="https://analyst.com/zoho-rev", title="Analyst Zoho")

    f1 = Fact(
        id="f-rev-1",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Revenue",
        value="₹100 Cr",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Zoho revenue touched ₹100 Cr.")],
    )
    f2 = Fact(
        id="f-rev-2",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Revenue",
        value="₹130 Cr",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Zoho revenue was estimated at ₹130 Cr.")],
    )

    conflicts_by_fact = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")

    assert len(conflicts_by_fact[f1.id]) == 1
    conflict = conflicts_by_fact[f1.id][0]

    # Verify both competing values are preserved with complete provenance
    assert conflict.entity == "Zoho"
    assert conflict.attribute == "Revenue"
    assert len(conflict.competing_values) == 2
    vals = {cv.value for cv in conflict.competing_values}
    assert vals == {"₹100 Cr", "₹130 Cr"}

    # Verify source linkage and evidence
    assert set(conflict.supporting_sources) == {"s1", "s2"}
    urls = {cv.source_url for cv in conflict.competing_values}
    assert urls == {"https://news.com/zoho-rev", "https://analyst.com/zoho-rev"}


def test_conflict_detection_textual_categorical_discrepancy():
    """Qualitative contradictions (e.g. Headquarters in Chennai vs Pleasanton) must be flagged."""
    detector = get_conflict_detector()

    s1 = Source(id="s1", research_run_id="run-1", url="https://site1.com", title="Site 1")
    s2 = Source(id="s2", research_run_id="run-1", url="https://site2.com", title="Site 2")

    f1 = Fact(
        id="f-hq-1",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Headquarters",
        value="Chennai, Tamil Nadu, India",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Global headquarters is in Chennai, Tamil Nadu.")],
    )
    f2 = Fact(
        id="f-hq-2",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Headquarters",
        value="Pleasanton, California, USA",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Headquartered out of Pleasanton, California.")],
    )

    conflicts = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")
    assert len(conflicts[f1.id]) == 1
    conflict = conflicts[f1.id][0]

    assert "Chennai" in conflict.description
    assert "Pleasanton" in conflict.description
    assert len(conflict.competing_values) == 2


def test_conflict_detection_binary_antonyms():
    """Binary/antonym contradictions (e.g. Free Tier Available vs No Free Tier) must be flagged."""
    detector = get_conflict_detector()

    s1 = Source(id="s1", research_run_id="run-1", url="https://site1.com", title="Site 1")
    s2 = Source(id="s2", research_run_id="run-1", url="https://site2.com", title="Site 2")

    f1 = Fact(
        id="f-tier-1",
        research_run_id="run-1",
        entity="Salesforce",
        attribute="Free Plan",
        value="Free tier available for up to 5 users",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Salesforce has a free tier available.")],
    )
    f2 = Fact(
        id="f-tier-2",
        research_run_id="run-1",
        entity="Salesforce",
        attribute="Free Plan",
        value="No free tier, paid subscription only",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="There is no free tier offered.")],
    )

    conflicts = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")
    assert len(conflicts[f1.id]) == 1
    assert "Contradictory values" in conflicts[f1.id][0].description


def test_conflict_detection_disclosure_discrepancy():
    """Concrete value vs 'Undisclosed / Contact Sales' should be identified as a disclosure conflict."""
    detector = get_conflict_detector()

    s1 = Source(id="s1", research_run_id="run-1", url="https://site1.com", title="Site 1")
    s2 = Source(id="s2", research_run_id="run-1", url="https://site2.com", title="Site 2")

    f1 = Fact(
        id="f-disc-1",
        research_run_id="run-1",
        entity="HubSpot",
        attribute="Enterprise Pricing",
        value="$1,200/mo base fee",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="HubSpot enterprise starts at $1,200/mo.")],
    )
    f2 = Fact(
        id="f-disc-2",
        research_run_id="run-1",
        entity="HubSpot",
        attribute="Enterprise Pricing",
        value="Undisclosed, contact sales for quote",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Pricing is undisclosed, contact sales.")],
    )

    conflicts = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")
    assert len(conflicts[f1.id]) == 1
    conflict = conflicts[f1.id][0]
    assert len(conflict.competing_values) == 2


def test_conflict_detection_ignores_formatting_equivalences():
    """Minor formatting or unit synonym differences must not produce false-positive conflicts."""
    detector = get_conflict_detector()

    s1 = Source(id="s1", research_run_id="run-1", url="https://site1.com", title="Site 1")
    s2 = Source(id="s2", research_run_id="run-1", url="https://site2.com", title="Site 2")

    f1 = Fact(
        id="f-eq-1",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Standard is ₹1,200/user/mo.")],
    )
    f2 = Fact(
        id="f-eq-2",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Pricing",
        value="1200 per user per month",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Costs 1200 per user per month.")],
    )

    conflicts = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")
    # Should NOT be flagged as conflict
    assert len(conflicts[f1.id]) == 0


def test_conflict_resolution_temporal_progression():
    """Discrepancies across significantly different publication dates are classified as EXPLAINED with temporal notes."""
    detector = get_conflict_detector()

    s1 = Source(
        id="s1",
        research_run_id="run-1",
        url="https://site1.com",
        title="2021 Report",
        published_at=datetime(2021, 1, 15, tzinfo=timezone.utc),
    )
    s2 = Source(
        id="s2",
        research_run_id="run-1",
        url="https://site2.com",
        title="2024 Report",
        published_at=datetime(2024, 6, 20, tzinfo=timezone.utc),
    )

    f1 = Fact(
        id="f-time-1",
        research_run_id="run-1",
        entity="Freshworks",
        attribute="Headcount",
        value="3,000 employees",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Freshworks has 3,000 employees in 2021.")],
    )
    f2 = Fact(
        id="f-time-2",
        research_run_id="run-1",
        entity="Freshworks",
        attribute="Headcount",
        value="5,200 employees",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Freshworks workforce reached 5,200 employees in 2024.")],
    )

    conflicts = detector.detect_conflicts([f1, f2], {"s1": s1, "s2": s2}, "run-1")
    assert len(conflicts[f1.id]) == 1
    conflict = conflicts[f1.id][0]

    assert conflict.status == ConflictStatus.EXPLAINED
    assert "Temporal progression" in conflict.resolution_note
    assert len(conflict.competing_values) == 2


def test_checker_integrates_conflict_detector_into_state():
    """Checker uses ConflictDetector to mark conflicting facts and emit Conflict records into batch result."""
    checker = get_checker()

    src1 = Source(id="s1", research_run_id="run-test", url="https://zoho.com", title="Zoho")
    src2 = Source(id="s2", research_run_id="run-test", url="https://analyst.com", title="Analyst")

    f1 = Fact(
        id="f1",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        source_ids=["s1"],
        evidence=[Evidence(source_id="s1", text="Standard is ₹1,200/user/mo.")],
    )
    f2 = Fact(
        id="f2",
        research_run_id="run-test",
        entity="Zoho",
        attribute="Pricing",
        value="₹3,500/user/mo",
        source_ids=["s2"],
        evidence=[Evidence(source_id="s2", text="Package is ₹3,500/user/mo.")],
    )

    batch = checker.check_all([f1, f2], [src1, src2], research_run_id="run-test")

    # Conflict records emitted
    assert len(batch.conflicts) == 1
    conflict = batch.conflicts[0]
    assert conflict.entity == "Zoho"
    assert conflict.attribute == "Pricing"

    # Both facts flagged CONFLICTING and YELLOW
    for f in batch.facts:
        assert f.verification_status == VerificationStatus.CONFLICTING
        assert f.trust_tag == TrustTag.YELLOW

    # State reducer merges conflict cleanly
    merged_conflicts = reduce_conflicts([], batch.conflicts)
    assert len(merged_conflicts) == 1
    assert merged_conflicts[0].id == conflict.id
