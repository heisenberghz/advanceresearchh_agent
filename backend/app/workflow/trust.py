"""Deterministic Trust Rules Engine for ResearchOps.

Specification: PRD.md Section 5, TECH_SPEC.md Section 13, AGENT_TASKS.md Task 14.
Implements explicit, deterministic, and configurable rules for assigning
trust tags (GREEN, YELLOW, RED) and verification statuses without relying
on LLM confidence or prose.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import TrustTag, VerificationStatus


class TrustRulesConfig(BaseModel):
    """Configurable thresholds for deterministic trust classification."""

    min_grounding_score: float = Field(
        default=0.5,
        description="Minimum ratio of matched value tokens required for evidence grounding",
    )
    authoritative_quality_threshold: float = Field(
        default=0.75,
        description="Minimum source quality score considered authoritative",
    )
    freshness_threshold: float = Field(
        default=0.70,
        description="Minimum freshness score considered sufficiently recent (<= 3 years)",
    )
    min_corroboration_count: int = Field(
        default=2,
        description="Minimum independent domains required for multi-source corroboration",
    )
    official_domain_score: float = Field(
        default=0.90,
        description="Quality threshold for recognizing official primary entity domain",
    )


class TrustScoreBreakdown(BaseModel):
    """Detailed, inspectable input metrics for a fact's verification."""

    source_exists: bool = Field(description="True if cited source exists in source registry")
    evidence_grounded: bool = Field(description="True if evidence text contains/matches claimed value")
    grounding_score: float = Field(ge=0.0, le=1.0, description="Token/substring match ratio")
    source_quality: float = Field(ge=0.0, le=1.0, description="Average quality score of supporting sources")
    freshness: float = Field(ge=0.0, le=1.0, description="Freshness score based on publication/retrieval")
    corroboration_count: int = Field(ge=0, description="Number of distinct supporting domains")
    has_conflict: bool = Field(default=False, description="True if conflicting values exist for this fact")
    is_primary_official: bool = Field(default=False, description="True if source is official entity domain")
    primary_domain: Optional[str] = Field(default=None, description="Main supporting domain name")
    conflict_summary: Optional[str] = Field(default=None, description="Summary of conflict if any")


class TrustEvaluation(BaseModel):
    """Deterministic output of the trust evaluation."""

    trust_tag: TrustTag
    status: VerificationStatus
    composite_score: float = Field(ge=0.0, le=1.0, description="Calculated overall reliability index")
    reason: str


def calculate_composite_score(breakdown: TrustScoreBreakdown) -> float:
    """Calculate a normalized reliability score (0.0 to 1.0) deterministically."""
    if not breakdown.source_exists or not breakdown.evidence_grounded:
        return 0.0

    # Weighting: Grounding (40%), Quality (25%), Freshness (15%), Corroboration (20%)
    corrob_normalized = min(1.0, breakdown.corroboration_count / 2.0)
    score = (
        0.40 * breakdown.grounding_score
        + 0.25 * breakdown.source_quality
        + 0.15 * breakdown.freshness
        + 0.20 * corrob_normalized
    )

    if breakdown.is_primary_official:
        score = min(1.0, score + 0.10)

    if breakdown.has_conflict:
        score = max(0.0, score - 0.20)

    return round(max(0.0, min(1.0, score)), 3)


def evaluate_trust(
    breakdown: TrustScoreBreakdown,
    config: Optional[TrustRulesConfig] = None,
) -> TrustEvaluation:
    """Evaluate a fact's metrics against explicit deterministic rules.

    Guarantees:
    - 100% deterministic (identical inputs always yield identical outputs).
    - No LLM prose or stochastic confidence overrides.
    - Inspectable reasoning and composite score returned.
    """
    cfg = config or TrustRulesConfig()
    composite = calculate_composite_score(breakdown)
    domain_str = breakdown.primary_domain or "unknown domain"

    # RULE 1: Source does not exist
    if not breakdown.source_exists:
        return TrustEvaluation(
            trust_tag=TrustTag.RED,
            status=VerificationStatus.UNSUPPORTED,
            composite_score=0.0,
            reason="Unsupported claim: Cited source record is missing or not found in verified registry.",
        )

    # RULE 2: Evidence snippet does not ground claimed value
    if not breakdown.evidence_grounded or breakdown.grounding_score < cfg.min_grounding_score:
        return TrustEvaluation(
            trust_tag=TrustTag.RED,
            status=VerificationStatus.UNSUPPORTED,
            composite_score=composite,
            reason=(
                f"Unsupported claim: Evidence snippet does not substantiate claimed value "
                f"(grounding score {breakdown.grounding_score:.2f} < {cfg.min_grounding_score:.2f})."
            ),
        )

    # RULE 3: Contradictory claims / conflict detected
    if breakdown.has_conflict:
        # Severe conflict with low quality sources gets RED
        if breakdown.source_quality < 0.50 or breakdown.grounding_score < 0.60:
            return TrustEvaluation(
                trust_tag=TrustTag.RED,
                status=VerificationStatus.CONFLICTING,
                composite_score=composite,
                reason=(
                    f"Conflicting and unverified: {breakdown.conflict_summary or 'Contradictory values detected with low source quality.'}"
                ),
            )
        return TrustEvaluation(
            trust_tag=TrustTag.YELLOW,
            status=VerificationStatus.CONFLICTING,
            composite_score=composite,
            reason=(
                f"Conflicting claims detected: {breakdown.conflict_summary or 'Contradictory claims preserved in conflict record.'}"
            ),
        )

    # RULE 4: Official Primary Domain (e.g. zoho.com for Zoho) -> GREEN
    if breakdown.is_primary_official and breakdown.source_quality >= cfg.official_domain_score:
        return TrustEvaluation(
            trust_tag=TrustTag.GREEN,
            status=VerificationStatus.VERIFIED,
            composite_score=composite,
            reason=(
                f"Verified: Directly substantiated by official primary source ({domain_str}) "
                f"with direct evidence match."
            ),
        )

    # RULE 5: Multi-source corroboration (>= min_corroboration_count) + high quality/freshness -> GREEN
    if breakdown.corroboration_count >= cfg.min_corroboration_count and (
        breakdown.source_quality >= cfg.authoritative_quality_threshold
        or breakdown.freshness >= cfg.freshness_threshold
    ):
        return TrustEvaluation(
            trust_tag=TrustTag.GREEN,
            status=VerificationStatus.VERIFIED,
            composite_score=composite,
            reason=(
                f"Verified: Corroborated across {breakdown.corroboration_count} independent sources "
                f"with strong credibility ({domain_str})."
            ),
        )

    # RULE 6: Single Authoritative Source + Fresh (e.g. SEC filing, Gartner, Reuters) -> GREEN
    if (
        breakdown.source_quality >= cfg.authoritative_quality_threshold
        and breakdown.freshness >= cfg.freshness_threshold
    ):
        return TrustEvaluation(
            trust_tag=TrustTag.GREEN,
            status=VerificationStatus.VERIFIED,
            composite_score=composite,
            reason=(
                f"Verified: Directly supported by authoritative publisher ({domain_str}) "
                f"with recent verified evidence."
            ),
        )

    # RULE 7: Single Secondary Source / Older / Moderate Authority -> YELLOW (Uncertain)
    if breakdown.freshness < cfg.freshness_threshold:
        reason_msg = f"Uncertain: Evidence substantiated by older source ({domain_str}) lacking recent corroboration."
    else:
        reason_msg = f"Uncertain: Single secondary source citation ({domain_str}) lacking multi-source corroboration."

    return TrustEvaluation(
        trust_tag=TrustTag.YELLOW,
        status=VerificationStatus.UNCERTAIN,
        composite_score=composite,
        reason=reason_msg,
    )

