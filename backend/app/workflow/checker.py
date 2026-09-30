"""Independent fact verification component (Checker).

Specification: PRD.md Section 5, TECH_SPEC.md Sections 11-14, AGENT_TASKS.md Task 13.
The Checker independently evaluates research facts against preserved evidence,
source metadata, authority, freshness, corroboration, and detects conflicts.
"""

from datetime import datetime, timezone
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.integrations.openrouter import OpenRouterClient
from app.models.conflict import CompetingValue, Conflict
from app.models.enums import ConflictStatus, TrustTag, VerificationStatus
from app.models.fact import Fact, VerificationResult
from app.models.source import Source
from app.workflow.conflicts import ConflictDetector, get_conflict_detector
from app.workflow.trust import (
    TrustRulesConfig,
    TrustScoreBreakdown,
    evaluate_trust,
)

logger = logging.getLogger("researchops.checker")



# High-credibility and authoritative domains
AUTHORITATIVE_DOMAINS: Set[str] = {
    # Financial & Business News
    "bloomberg.com",
    "reuters.com",
    "wsj.com",
    "ft.com",
    "forbes.com",
    "cnbc.com",
    "economictimes.indiatimes.com",
    "business-standard.com",
    "livemint.com",
    "techcrunch.com",
    "venturebeat.com",
    "theverge.com",
    # Research & Analyst Firms
    "gartner.com",
    "forrester.com",
    "statista.com",
    "idc.com",
    "mckinsey.com",
    # Official / Regulators / Reference
    "sec.gov",
    "mca.gov.in",
    "wikipedia.org",
    # Software Review Aggregators
    "g2.com",
    "capterra.com",
    "trustradius.com",
}


def extract_domain(url: str) -> str:
    """Extract clean lowercase domain from URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def clean_normalized_text(text: str) -> str:
    """Normalize text for invariant comparison."""
    if not text:
        return ""
    text = text.lower()
    # Normalize common abbreviations
    text = re.sub(r"\bper month\b|\bmonth\b|\b/mo\b", "/mo", text)
    text = re.sub(r"\bper user\b|\buser\b", "user", text)
    # Remove punctuation except / and decimals
    text = re.sub(r"[,\$₹€£]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_numeric_tokens(val: str) -> List[str]:
    """Extract all standalone numbers and percentages from a value string."""
    return re.findall(r"\b\d+(?:\.\d+)?%?\b", val.replace(",", ""))


class CheckerBatchResult(BaseModel):
    """Aggregate output of batch fact verification."""

    facts: List[Fact] = Field(description="Updated facts with trust tags and verification reasons")
    verification_results: List[VerificationResult] = Field(description="Individual verification records")
    conflicts: List[Conflict] = Field(default_factory=list, description="Preserved conflict records")


class Checker:
    """Independent fact verification engine.
    
    Evaluates:
    1. Source existence in verified source registry.
    2. Evidence grounding (verbatim value and attribute presence).
    3. Source authority and entity primary-source matching.
    4. Information freshness based on publication/retrieval dates.
    5. Multi-source corroboration.
    6. Inter-fact contradiction / conflict detection.
    """

    def __init__(
        self,
        openrouter_client: Optional[OpenRouterClient] = None,
        trust_config: Optional[TrustRulesConfig] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        self.openrouter_client = openrouter_client
        self.trust_config = trust_config or TrustRulesConfig()
        self.conflict_detector = conflict_detector or get_conflict_detector()



    def evaluate_source_quality(self, entity: str, source: Source) -> Tuple[float, bool]:
        """Compute authority score (0.0 - 1.0) and whether it is the official primary domain."""
        domain = source.domain or extract_domain(source.url)
        clean_entity = re.sub(r"[^a-zA-Z0-9]", "", entity.lower())

        # Check if domain belongs to the official entity (e.g. zoho.com for Zoho)
        is_primary = False
        if clean_entity and len(clean_entity) >= 3 and clean_entity in domain:
            is_primary = True
            return 0.95, is_primary

        if domain in AUTHORITATIVE_DOMAINS or domain.endswith((".gov", ".edu")):
            return 0.85, False
        if domain.endswith(".org"):
            return 0.75, False
        if domain:
            return 0.55, False
        return 0.20, False

    def evaluate_freshness(self, fact: Fact, sources: List[Source]) -> float:
        """Compute freshness score (0.0 - 1.0)."""
        pub_date = fact.published_at
        if not pub_date:
            for s in sources:
                if s.published_at:
                    pub_date = s.published_at
                    break

        if pub_date:
            now = datetime.now(timezone.utc)
            # Ensure timezone awareness
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_days = (now - pub_date).days
            if age_days <= 365:
                return 1.0
            if age_days <= 730:
                return 0.85
            if age_days <= 1095:
                return 0.70
            return 0.40

        # No publication timestamp, but recently retrieved from web search
        return 0.75


    def check_evidence_grounding(self, fact: Fact) -> Tuple[bool, float, str]:
        """Verify whether preserved evidence snippets corroborate the fact value."""
        if not fact.evidence:
            return False, 0.0, "No evidence snippet attached to fact"

        raw_combined = " ".join(e.text for e in fact.evidence if e.text)
        if not raw_combined.strip():
            return False, 0.0, "Evidence snippets are empty or whitespace"

        combined_clean = clean_normalized_text(raw_combined)
        value_clean = clean_normalized_text(fact.value)

        # 1. Direct normalized substring match
        if value_clean and value_clean in combined_clean:
            return True, 1.0, "Exact value substring verified in evidence"

        # 2. Numeric check: If the value specifies numbers (e.g. pricing, founded year, metrics)
        value_numbers = extract_numeric_tokens(fact.value)
        if value_numbers:
            evidence_numbers = extract_numeric_tokens(raw_combined)
            missing_nums = [n for n in value_numbers if n not in evidence_numbers]
            if missing_nums:
                return (
                    False,
                    0.2,
                    f"Claimed numeric values {missing_nums} not found in evidence text",
                )

        # 3. Key content terms check
        val_tokens = [
            t for t in re.findall(r"\b[a-zA-Z0-9]{3,}\b", value_clean)
            if t not in {"the", "and", "for", "with", "user", "per"}
        ]
        if val_tokens:
            matched_tokens = [
                t for t in val_tokens
                if t in combined_clean or t in raw_combined.lower()
            ]
            ratio = len(matched_tokens) / len(val_tokens)
            if ratio >= 0.5:
                return True, ratio, "Evidence matches key value components"
            return False, ratio, f"Evidence only matches {len(matched_tokens)}/{len(val_tokens)} tokens of value"

        # 4. Fallback: match any key word from value
        if any(w in combined_clean for w in value_clean.split() if len(w) >= 3):
            return True, 0.6, "Partial value components matched in evidence"

        return False, 0.0, "Evidence does not corroborate extracted value"

    def detect_conflicts(
        self,
        facts: List[Fact],
        sources_map: Dict[str, Source],
        research_run_id: str,
    ) -> Dict[str, List[Conflict]]:
        """Detect and preserve conflicting claims across facts for the same entity and attribute."""
        return self.conflict_detector.detect_conflicts(facts, sources_map, research_run_id)


    def verify_fact(
        self,
        fact: Fact,
        sources_map: Dict[str, Source],
        detected_conflicts: Optional[List[Conflict]] = None,
    ) -> VerificationResult:
        """Independently evaluate a single fact against evidence and sources."""
        conflicts = detected_conflicts or []
        conflict_ids = [c.id for c in conflicts]

        # 1. Source existence check
        valid_sources: List[Source] = []
        for s_id in fact.source_ids:
            if s_id in sources_map:
                valid_sources.append(sources_map[s_id])

        # 2. Evidence grounding check
        is_grounded, ground_score, ground_note = self.check_evidence_grounding(fact)

        # 3. Source Quality and Primary Domain Evaluation
        domains: Set[str] = set()
        has_primary_official = False
        quality_scores: List[float] = []

        for s in valid_sources:
            q_score, is_prim = self.evaluate_source_quality(fact.entity, s)
            quality_scores.append(q_score)
            if is_prim:
                has_primary_official = True
            domain = s.domain or extract_domain(s.url)
            if domain:
                domains.add(domain)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        freshness_score = self.evaluate_freshness(fact, valid_sources)
        corroboration_count = len(domains)
        primary_domain = next(iter(domains)) if domains else "unknown"

        # 4. Construct inspectable breakdown & evaluate deterministic trust rules
        breakdown = TrustScoreBreakdown(
            source_exists=bool(valid_sources),
            evidence_grounded=is_grounded,
            grounding_score=ground_score,
            source_quality=avg_quality,
            freshness=freshness_score,
            corroboration_count=corroboration_count,
            has_conflict=bool(conflicts),
            is_primary_official=has_primary_official,
            primary_domain=primary_domain,
            conflict_summary="; ".join(c.description for c in conflicts) if conflicts else None,
        )

        evaluation = evaluate_trust(breakdown, self.trust_config)

        # Only cite supporting sources if source exists and is grounded
        supporting = [s.id for s in valid_sources] if (valid_sources and is_grounded) else []

        return VerificationResult(
            fact_id=fact.id,
            status=evaluation.status,
            trust_tag=evaluation.trust_tag,
            reason=evaluation.reason,
            supporting_sources=supporting,
            conflicts=conflict_ids,
        )


    def check_all(
        self,
        facts: List[Fact],
        sources: List[Source],
        research_run_id: Optional[str] = None,
    ) -> CheckerBatchResult:
        """Run batch verification over all collected facts and sources."""
        run_id = research_run_id or (facts[0].research_run_id if facts else "run-default")
        sources_map: Dict[str, Source] = {s.id: s for s in sources}

        # Step 1: Detect conflicts across all facts
        conflicts_by_fact = self.detect_conflicts(facts, sources_map, run_id)
        all_conflicts_map: Dict[str, Conflict] = {}
        for c_list in conflicts_by_fact.values():
            for c in c_list:
                all_conflicts_map[c.id] = c

        # Step 2: Independently verify each fact
        verified_facts: List[Fact] = []
        verification_results: List[VerificationResult] = []

        now = datetime.now(timezone.utc)
        for fact in facts:
            fact_confs = conflicts_by_fact.get(fact.id, [])
            res = self.verify_fact(fact, sources_map, fact_confs)

            # Update fact fields in place while preserving all evidence
            fact.verification_status = res.status
            fact.trust_tag = res.trust_tag
            fact.verification_reason = res.reason
            fact.updated_at = now

            verified_facts.append(fact)
            verification_results.append(res)

        logger.info(
            "Checker finished run %s: %d facts evaluated, %d verified (GREEN), %d uncertain (YELLOW), %d unsupported (RED), %d conflicts",
            run_id,
            len(verified_facts),
            sum(1 for f in verified_facts if f.trust_tag == TrustTag.GREEN),
            sum(1 for f in verified_facts if f.trust_tag == TrustTag.YELLOW),
            sum(1 for f in verified_facts if f.trust_tag == TrustTag.RED),
            len(all_conflicts_map),
        )

        return CheckerBatchResult(
            facts=verified_facts,
            verification_results=verification_results,
            conflicts=list(all_conflicts_map.values()),
        )


def get_checker(
    trust_config: Optional[TrustRulesConfig] = None,
    conflict_detector: Optional[ConflictDetector] = None,
) -> Checker:
    """Factory creating default Checker instance."""
    return Checker(trust_config=trust_config, conflict_detector=conflict_detector)


