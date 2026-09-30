"""Unit tests for deterministic trust rules (Task 14)."""

import pytest

from app.models.enums import TrustTag, VerificationStatus
from app.workflow.trust import (
    TrustEvaluation,
    TrustRulesConfig,
    TrustScoreBreakdown,
    calculate_composite_score,
    evaluate_trust,
)


def test_trust_rules_missing_source_yields_red():
    """If cited source is missing, the fact must be classified as RED and UNSUPPORTED."""
    breakdown = TrustScoreBreakdown(
        source_exists=False,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.8,
        freshness=0.9,
        corroboration_count=1,
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.RED
    assert result.status == VerificationStatus.UNSUPPORTED
    assert result.composite_score == 0.0
    assert "source record is missing or not found" in result.reason


def test_trust_rules_ungrounded_evidence_yields_red():
    """If evidence does not ground the value (or falls below threshold), classify as RED and UNSUPPORTED."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=False,
        grounding_score=0.2,
        source_quality=0.9,
        freshness=0.9,
        corroboration_count=1,
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.RED
    assert result.status == VerificationStatus.UNSUPPORTED
    assert "does not substantiate claimed value" in result.reason


def test_trust_rules_official_primary_domain_yields_green():
    """Primary official entity domain directly grounds fact with GREEN and VERIFIED."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.95,
        freshness=0.85,
        corroboration_count=1,
        is_primary_official=True,
        primary_domain="zoho.com",
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.GREEN
    assert result.status == VerificationStatus.VERIFIED
    assert result.composite_score >= 0.80
    assert "official primary source" in result.reason
    assert "zoho.com" in result.reason



def test_trust_rules_corroborated_sources_yields_green():
    """Multi-source corroboration (>= 2 distinct domains) with high quality yields GREEN and VERIFIED."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.85,
        freshness=0.80,
        corroboration_count=2,
        primary_domain="reuters.com",
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.GREEN
    assert result.status == VerificationStatus.VERIFIED
    assert "Corroborated across 2 independent sources" in result.reason


def test_trust_rules_single_authoritative_fresh_yields_green():
    """Single source from an authoritative publisher (e.g. SEC, Reuters) with recent freshness yields GREEN."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.85,
        freshness=0.85,
        corroboration_count=1,
        primary_domain="bloomberg.com",
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.GREEN
    assert result.status == VerificationStatus.VERIFIED
    assert "Directly supported by authoritative publisher" in result.reason


def test_trust_rules_single_secondary_source_yields_yellow():
    """Single non-authoritative secondary source with grounded evidence yields YELLOW and UNCERTAIN."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=0.8,
        source_quality=0.55,
        freshness=0.75,
        corroboration_count=1,
        primary_domain="techblog.io",
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.YELLOW
    assert result.status == VerificationStatus.UNCERTAIN
    assert "Single secondary source citation" in result.reason


def test_trust_rules_older_source_yields_yellow():
    """Evidence substantiated by older source (< freshness threshold) yields YELLOW with freshness notice."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.60,
        freshness=0.40,  # Older than 3 years
        corroboration_count=1,
        primary_domain="archivedtech.org",
    )
    result: TrustEvaluation = evaluate_trust(breakdown)

    assert result.trust_tag == TrustTag.YELLOW
    assert result.status == VerificationStatus.UNCERTAIN
    assert "older source" in result.reason


def test_trust_rules_conflict_classification():
    """Conflict detection: grounded conflict yields YELLOW; low quality conflict yields RED."""
    # Case A: Grounded conflict with moderate quality sources
    conflict_breakdown_yellow = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=0.9,
        source_quality=0.7,
        freshness=0.8,
        corroboration_count=1,
        has_conflict=True,
        conflict_summary="Contradictory pricing values: ₹1,200 vs ₹3,500",
    )
    res_yellow = evaluate_trust(conflict_breakdown_yellow)
    assert res_yellow.trust_tag == TrustTag.YELLOW
    assert res_yellow.status == VerificationStatus.CONFLICTING
    assert "Contradictory pricing values" in res_yellow.reason

    # Case B: Severe conflict with low quality / ungrounded claims
    conflict_breakdown_red = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=0.5,
        source_quality=0.3,
        freshness=0.5,
        corroboration_count=1,
        has_conflict=True,
        conflict_summary="Severe contradiction from unvetted sources",
    )
    res_red = evaluate_trust(conflict_breakdown_red)
    assert res_red.trust_tag == TrustTag.RED
    assert res_red.status == VerificationStatus.CONFLICTING
    assert "Conflicting and unverified" in res_red.reason


def test_trust_rules_configurable_thresholds():
    """Rules engine respects custom configurable thresholds."""
    # Under default config (min_corroboration_count=2), 1 source isn't corroborated
    strict_config = TrustRulesConfig(
        min_corroboration_count=3,
        authoritative_quality_threshold=0.90,
    )

    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=1.0,
        source_quality=0.80,  # Below strict 0.90
        freshness=0.80,
        corroboration_count=2,  # Below strict 3
        primary_domain="techsite.com",
    )

    result = evaluate_trust(breakdown, config=strict_config)
    # Under strict config, should be downgraded to YELLOW
    assert result.trust_tag == TrustTag.YELLOW
    assert result.status == VerificationStatus.UNCERTAIN


def test_trust_rules_deterministic_and_idempotent():
    """Evaluation must be 100% deterministic: identical inputs yield identical outputs."""
    breakdown = TrustScoreBreakdown(
        source_exists=True,
        evidence_grounded=True,
        grounding_score=0.95,
        source_quality=0.85,
        freshness=0.85,
        corroboration_count=2,
        primary_domain="reuters.com",
    )

    eval1 = evaluate_trust(breakdown)
    eval2 = evaluate_trust(breakdown)

    assert eval1.trust_tag == eval2.trust_tag
    assert eval1.status == eval2.status
    assert eval1.composite_score == eval2.composite_score
    assert eval1.reason == eval2.reason
