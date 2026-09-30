"""Conflict Detection & Resolution Engine for ResearchOps.

Specification: PRD.md Section 5, TECH_SPEC.md Section 14, AGENT_TASKS.md Task 15.
Detects, preserves, and categorizes contradictory claims between multiple research sources.
Invariant: Never silently discard conflicting evidence; preserve all competing values,
sources, and verbatim excerpts with complete provenance.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from app.models.conflict import CompetingValue, Conflict
from app.models.enums import ConflictStatus
from app.models.fact import Fact
from app.models.source import Source

logger = logging.getLogger("researchops.conflicts")


class ConflictType(str, Enum):
    """Classification of the nature of contradiction."""

    NUMERIC = "numeric"
    TEXTUAL = "textual"
    DISCLOSURE_DISCREPANCY = "disclosure_discrepancy"
    TEMPORAL_PROGRESSION = "temporal_progression"


# Common indicator phrases for unannounced / private / contact sales metrics
UNDISCLOSED_PATTERNS: Set[str] = {
    "undisclosed",
    "not disclosed",
    "not publicly available",
    "contact sales",
    "quote only",
    "pricing on request",
    "n/a",
    "unknown",
    "custom pricing",
    "not available",
}

# Binary and direct antonym pairs for categorical conflicts
ANTONYM_PAIRS: List[Tuple[Set[str], Set[str]]] = [
    ({"public", "publicly traded", "listed", "nyse", "nasdaq"}, {"private", "privately held", "bootstrapped"}),
    ({"free", "freemium", "free tier"}, {"paid only", "no free tier", "subscription only"}),
    ({"open source", "open-source", "foss"}, {"proprietary", "closed source", "closed-source"}),
    ({"supported", "yes", "available", "included"}, {"unsupported", "no", "not supported", "lacking"}),
]


def clean_text_for_comparison(val: str) -> str:
    """Normalize text removing punctuation, symbols, and irregular spacing."""
    if not val:
        return ""
    val = val.lower().strip()
    val = re.sub(r"[,\$₹€£%]", "", val)
    val = re.sub(r"\bper month\b|\bmonth\b|\b/mo\b", "/mo", val)
    val = re.sub(r"\bper user\b|\buser\b", "user", val)
    return re.sub(r"\s+", " ", val).strip()


def parse_numeric_values(val: str) -> List[float]:
    """Extract standalone numbers as floats, handling multiplier suffixes (K, M, B, Cr, Lakh)."""
    cleaned = val.replace(",", "")
    numbers: List[float] = []

    # Detect Indian numbering system (Crore, Lakh)
    cr_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)\b", cleaned, re.IGNORECASE)
    for m in cr_match:
        numbers.append(float(m) * 10_000_000)

    lakh_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)\b", cleaned, re.IGNORECASE)
    for m in lakh_match:
        numbers.append(float(m) * 100_000)

    # Detect International multipliers (Billion, Million, Thousand)
    b_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:b|billion|billions)\b", cleaned, re.IGNORECASE)
    for m in b_match:
        numbers.append(float(m) * 1_000_000_000)

    m_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:m|million|millions)\b", cleaned, re.IGNORECASE)
    for m in m_match:
        numbers.append(float(m) * 1_000_000)

    # Standard numbers
    raw_nums = re.findall(r"\b\d+(?:\.\d+)?\b", cleaned)
    for n in raw_nums:
        try:
            numbers.append(float(n))
        except ValueError:
            pass

    return numbers


class ConflictDetector:
    """Deterministic Conflict Detection & Resolution engine."""

    def is_disclosure_conflict(self, val1: str, val2: str) -> Tuple[bool, Optional[str]]:
        """Detect conflict where one source provides a concrete metric while another claims undisclosed/contact sales."""
        c1 = val1.lower().strip()
        c2 = val2.lower().strip()

        is_c1_undisclosed = any(p in c1 for p in UNDISCLOSED_PATTERNS)
        is_c2_undisclosed = any(p in c2 for p in UNDISCLOSED_PATTERNS)

        if is_c1_undisclosed != is_c2_undisclosed:
            concrete = val1 if not is_c1_undisclosed else val2
            undisclosed = val2 if not is_c1_undisclosed else val1
            return (
                True,
                f"Disclosure discrepancy: One source asserts concrete value '{concrete}', "
                f"while another reports '{undisclosed}'.",
            )
        return False, None

    def is_numeric_conflict(self, val1: str, val2: str) -> Tuple[bool, Optional[str]]:
        """Detect quantitative contradictions beyond standard rounding tolerances."""
        nums1 = parse_numeric_values(val1)
        nums2 = parse_numeric_values(val2)

        if not nums1 or not nums2:
            return False, None

        # Compare primary numbers
        primary1 = nums1[0]
        primary2 = nums2[0]

        if primary1 == primary2:
            return False, None

        # Tolerance: if values differ by more than 2%
        diff_pct = abs(primary1 - primary2) / max(primary1, primary2)
        if diff_pct > 0.02:
            return (
                True,
                f"Numeric divergence: '{val1}' ({primary1:g}) vs '{val2}' ({primary2:g}) "
                f"exceeds tolerance ({diff_pct * 100:.1f}% discrepancy).",
            )

        return False, None

    def is_textual_conflict(self, val1: str, val2: str) -> Tuple[bool, Optional[str]]:
        """Detect categorical or qualitative contradictions."""
        c1 = clean_text_for_comparison(val1)
        c2 = clean_text_for_comparison(val2)

        if not c1 or not c2 or c1 == c2:
            return False, None

        # 1. Antonym / binary check
        for group_a, group_b in ANTONYM_PAIRS:
            in_a1 = any(term in c1 for term in group_a)
            in_b2 = any(term in c2 for term in group_b)
            in_b1 = any(term in c1 for term in group_b)
            in_a2 = any(term in c2 for term in group_a)

            if (in_a1 and in_b2) or (in_b1 and in_a2):
                return (
                    True,
                    f"Categorical opposition: '{val1}' directly contradicts '{val2}'.",
                )

        # 2. Mutually exclusive entity properties (e.g. distinct cities for headquarters)
        # If neither is a substring of the other and both have non-numeric words
        if c1 not in c2 and c2 not in c1:
            words1 = set(re.findall(r"\b[a-zA-Z]{3,}\b", c1))
            words2 = set(re.findall(r"\b[a-zA-Z]{3,}\b", c2))
            overlap = words1.intersection(words2)
            # If low overlap (< 30%) and both specify substantive claims
            if words1 and words2 and (len(overlap) / max(len(words1), len(words2))) < 0.30:
                return (
                    True,
                    f"Qualitative discrepancy: Distinct assertions '{val1}' vs '{val2}'.",
                )

        return False, None

    def check_pair_conflict(self, f1: Fact, f2: Fact) -> Tuple[bool, Optional[ConflictType], Optional[str]]:
        """Evaluate whether two facts for the same entity and attribute contradict each other."""
        # 1. Disclosure / transparency discrepancy
        is_disc, disc_desc = self.is_disclosure_conflict(f1.value, f2.value)
        if is_disc:
            return True, ConflictType.DISCLOSURE_DISCREPANCY, disc_desc

        # 2. Numeric conflict
        is_num, num_desc = self.is_numeric_conflict(f1.value, f2.value)
        if is_num:
            return True, ConflictType.NUMERIC, num_desc

        # 3. Categorical / textual conflict
        is_txt, txt_desc = self.is_textual_conflict(f1.value, f2.value)
        if is_txt:
            return True, ConflictType.TEXTUAL, txt_desc

        return False, None, None

    def analyze_resolution_context(
        self,
        f1: Fact,
        f2: Fact,
        s1: Optional[Source],
        s2: Optional[Source],
    ) -> Tuple[ConflictStatus, Optional[str]]:
        """Examine contextual factors (e.g. publication dates or product tiers) to explain the discrepancy."""
        d1 = f1.published_at or (s1.published_at if s1 else None)
        d2 = f2.published_at or (s2.published_at if s2 else None)

        # Temporal analysis: If sources have different publication dates
        if d1 and d2:
            if d1.tzinfo is None:
                d1 = d1.replace(tzinfo=timezone.utc)
            if d2.tzinfo is None:
                d2 = d2.replace(tzinfo=timezone.utc)

            date_diff = abs((d1 - d2).days)
            if date_diff >= 180:  # 6+ months apart
                older_date = min(d1, d2).strftime("%Y-%m")
                newer_date = max(d1, d2).strftime("%Y-%m")
                older_val = f1.value if d1 < d2 else f2.value
                newer_val = f2.value if d1 < d2 else f1.value
                return (
                    ConflictStatus.EXPLAINED,
                    (
                        f"Temporal progression: Earlier report ({older_date}) cited '{older_val}', "
                        f"whereas updated report ({newer_date}) cited '{newer_val}'. Both preserved."
                    ),
                )

        # Tier / scope analysis: inspect evidence for tier indicators
        ev1 = (f1.evidence[0].text if f1.evidence else "").lower()
        ev2 = (f2.evidence[0].text if f2.evidence else "").lower()

        tiers = ["standard", "starter", "professional", "enterprise", "ultimate", "basic"]
        tier1 = next((t for t in tiers if t in ev1 or t in f1.value.lower()), None)
        tier2 = next((t for t in tiers if t in ev2 or t in f2.value.lower()), None)

        if tier1 and tier2 and tier1 != tier2:
            return (
                ConflictStatus.EXPLAINED,
                (
                    f"Tier variation: Value '{f1.value}' corresponds to {tier1.title()} tier, "
                    f"whereas '{f2.value}' corresponds to {tier2.title()} tier. Both preserved."
                ),
            )

        return (
            ConflictStatus.UNRESOLVED,
            "Direct contradiction between sources without clear temporal or tier distinction. Both values preserved.",
        )

    def detect_conflicts(
        self,
        facts: List[Fact],
        sources_map: Dict[str, Source],
        research_run_id: str,
    ) -> Dict[str, List[Conflict]]:
        """Detect and preserve all conflicting claims across facts.
        
        Returns:
            Mapping from fact.id -> list of Conflict records involving that fact.
        """
        groups: Dict[Tuple[str, str], List[Fact]] = {}
        for f in facts:
            key = (f.entity.strip().lower(), f.attribute.strip().lower())
            groups.setdefault(key, []).append(f)

        fact_conflicts: Dict[str, List[Conflict]] = {f.id: [] for f in facts}

        for (entity_key, attr_key), group in groups.items():
            if len(group) < 2:
                continue

            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    f1 = group[i]
                    f2 = group[j]

                    is_conflict, conflict_type, conflict_desc = self.check_pair_conflict(f1, f2)
                    if not is_conflict:
                        continue

                    src_id1 = f1.source_ids[0] if f1.source_ids else None
                    src_id2 = f2.source_ids[0] if f2.source_ids else None
                    s1 = sources_map.get(src_id1) if src_id1 else None
                    s2 = sources_map.get(src_id2) if src_id2 else None

                    status, resolution_note = self.analyze_resolution_context(f1, f2, s1, s2)

                    ev1 = f1.evidence[0].text if f1.evidence else None
                    ev2 = f2.evidence[0].text if f2.evidence else None

                    conflict = Conflict(
                        id=f"conf-{f1.id[:6]}-{f2.id[:6]}",
                        research_run_id=research_run_id,
                        entity=f1.entity,
                        attribute=f1.attribute,
                        description=(
                            f"Contradictory values for {f1.entity} ({f1.attribute}): "
                            f"'{f1.value}' vs '{f2.value}'"
                        ),
                        status=status,
                        resolution_note=resolution_note,
                        competing_values=[
                            CompetingValue(
                                value=f1.value,
                                source_id=src_id1,
                                source_url=s1.url if s1 else None,
                                evidence=ev1,
                            ),
                            CompetingValue(
                                value=f2.value,
                                source_id=src_id2,
                                source_url=s2.url if s2 else None,
                                evidence=ev2,
                            ),
                        ],
                        supporting_sources=[s for s in [src_id1, src_id2] if s],
                    )

                    fact_conflicts[f1.id].append(conflict)
                    fact_conflicts[f2.id].append(conflict)
                    logger.warning(
                        "Conflict detected on %s (%s) [%s]: '%s' vs '%s'",
                        f1.entity,
                        f1.attribute,
                        status.value,
                        f1.value,
                        f2.value,
                    )

        return fact_conflicts


def get_conflict_detector() -> ConflictDetector:
    """Factory creating default ConflictDetector instance."""
    return ConflictDetector()
