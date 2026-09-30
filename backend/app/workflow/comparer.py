"""Comparer module creating structured comparison matrices from verified research findings.

Specification: PRD.md Section 5.4, TECH_SPEC.md Section 20, and AGENT_TASKS.md Task 18.
Key invariants:
- Group facts by entity and by metric.
- Preserve fact and source references for complete auditability.
- Represent missing values clearly as "Not found" linked to ResearchGap records where applicable.
- Preserve trust tags (GREEN, YELLOW, RED).
- NEVER invent or fabricate missing values.
"""

import logging
from typing import Dict, List, Optional, Tuple

from app.models.comparison import ComparisonCell, ComparisonMatrix
from app.models.conflict import Conflict
from app.models.enums import TrustTag
from app.models.fact import Fact
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.workflow.state import ResearchState

logger = logging.getLogger("researchops.comparer")


class Comparer:
    """Creates structured entity-by-dimension comparison matrices from verified facts and research gaps."""

    def __init__(self) -> None:
        pass

    def build_matrix(
        self,
        facts: List[Fact],
        entities: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        gaps: Optional[List[ResearchGap]] = None,
        conflicts: Optional[List[Conflict]] = None,
        jobs: Optional[List[ResearchJob]] = None,
    ) -> ComparisonMatrix:
        """Construct a structured ComparisonMatrix aligning entities and dimensions.

        Args:
            facts: Verified or unverified extracted facts.
            entities: Optional list of target entities to compare.
            metrics: Optional list of specific comparison dimensions.
            gaps: Optional list of identified research gaps.
            conflicts: Optional list of detected contradictions.
            jobs: Optional list of research jobs (used for metric discovery).

        Returns:
            Populated ComparisonMatrix containing cells for all (entity, metric) combinations.
        """
        gaps = gaps or []
        conflicts = conflicts or []
        jobs = jobs or []

        # 1. Resolve & Canonicalize Entities
        canonical_entities: List[str] = []
        entity_name_map: Dict[str, str] = {}  # lowercase -> canonical casing

        for ent in entities or []:
            e_clean = (ent or "").strip()
            if e_clean and e_clean.lower() not in entity_name_map:
                canonical_entities.append(e_clean)
                entity_name_map[e_clean.lower()] = e_clean

        for f in facts:
            e_clean = (f.entity or "").strip()
            if e_clean and e_clean.lower() not in entity_name_map:
                canonical_entities.append(e_clean)
                entity_name_map[e_clean.lower()] = e_clean

        for j in jobs:
            e_clean = (j.entity or "").strip()
            if e_clean and e_clean.lower() not in entity_name_map:
                canonical_entities.append(e_clean)
                entity_name_map[e_clean.lower()] = e_clean

        # 2. Resolve & Canonicalize Metrics / Dimensions
        canonical_metrics: List[str] = []
        metric_name_map: Dict[str, str] = {}  # lowercase -> canonical casing

        for m in metrics or []:
            m_clean = (m or "").strip()
            if m_clean and m_clean.lower() not in metric_name_map:
                canonical_metrics.append(m_clean)
                metric_name_map[m_clean.lower()] = m_clean

        # Discover metrics from jobs
        for j in jobs:
            attr = (j.attribute or "").strip()
            if attr and attr.lower() not in metric_name_map:
                canonical_metrics.append(attr)
                metric_name_map[attr.lower()] = attr

        # Discover metrics from facts
        for f in facts:
            attr = (f.attribute or "").strip()
            if attr and attr.lower() not in metric_name_map:
                canonical_metrics.append(attr)
                metric_name_map[attr.lower()] = attr

        # Fallback if no metrics found
        if not canonical_metrics:
            canonical_metrics = ["Overview"]

        # 3. Index Facts by (entity_lower, metric_lower)
        facts_by_pair: Dict[Tuple[str, str], List[Fact]] = {}
        for f in facts:
            e_key = (f.entity or "").strip().lower()
            m_key = (f.attribute or "").strip().lower()
            facts_by_pair.setdefault((e_key, m_key), []).append(f)

        # Index Gaps by (entity_lower, metric_lower)
        gaps_by_pair: Dict[Tuple[str, str], ResearchGap] = {}
        for g in gaps:
            req = g.requested_information.lower()
            for e_low in entity_name_map:
                if e_low in req:
                    for m_low in metric_name_map:
                        if m_low in req:
                            gaps_by_pair[(e_low, m_low)] = g
                            break

        # Index Conflicts by (entity_lower, metric_lower)
        conflicts_by_pair: Dict[Tuple[str, str], Conflict] = {}
        for c in conflicts:
            e_key = (c.entity or "").strip().lower()
            m_key = (c.attribute or "").strip().lower()
            if e_key and m_key:
                conflicts_by_pair[(e_key, m_key)] = c

        # 4. Construct Matrix Cells
        cells: List[ComparisonCell] = []

        for entity in canonical_entities:
            e_low = entity.lower()
            for metric in canonical_metrics:
                m_low = metric.lower()
                pair_facts = facts_by_pair.get((e_low, m_low), [])

                if pair_facts:
                    # Select the best fact based on verification quality: GREEN > YELLOW > RED
                    def fact_sort_key(f: Fact) -> int:
                        if f.trust_tag == TrustTag.GREEN:
                            return 3
                        if f.trust_tag == TrustTag.YELLOW:
                            return 2
                        return 1

                    sorted_facts = sorted(pair_facts, key=fact_sort_key, reverse=True)
                    best_fact = sorted_facts[0]

                    # Check if there is an associated conflict
                    conflict_note: Optional[str] = None
                    if (e_low, m_low) in conflicts_by_pair:
                        c = conflicts_by_pair[(e_low, m_low)]
                        conflict_note = f"Conflict detected: {c.description}"

                    # Collect all supporting source IDs across the facts for this metric
                    all_source_ids: List[str] = []
                    for f in pair_facts:
                        for sid in f.source_ids:
                            if sid not in all_source_ids:
                                all_source_ids.append(sid)

                    cells.append(
                        ComparisonCell(
                            entity=entity,
                            metric=metric,
                            value=best_fact.value,
                            trust_tag=best_fact.trust_tag,
                            fact_id=best_fact.id,
                            source_ids=all_source_ids,
                            notes=conflict_note,
                        )
                    )
                else:
                    # Missing value: check if explicit ResearchGap exists
                    gap = gaps_by_pair.get((e_low, m_low))
                    gap_id = gap.id if gap else None
                    gap_note = gap.reason if gap else "No verified information located."

                    cells.append(
                        ComparisonCell(
                            entity=entity,
                            metric=metric,
                            value="Not found",
                            trust_tag=TrustTag.RED,
                            fact_id=None,
                            source_ids=[],
                            gap_id=gap_id,
                            notes=gap_note,
                        )
                    )

        matrix = ComparisonMatrix(
            entities=canonical_entities,
            metrics=canonical_metrics,
            cells=cells,
        )
        logger.info(
            "[Comparer] Built ComparisonMatrix: %d entities x %d metrics (%d cells)",
            len(canonical_entities),
            len(canonical_metrics),
            len(cells),
        )
        return matrix

    def compare(self, state: ResearchState) -> ComparisonMatrix:
        """Create a ComparisonMatrix directly from a ResearchState container."""
        return self.build_matrix(
            facts=state.get("facts", []),
            entities=state.get("entities", []),
            metrics=None,
            gaps=state.get("gaps", []),
            conflicts=state.get("conflicts", []),
            jobs=state.get("research_jobs", []),
        )


_COMPARER_INSTANCE: Optional[Comparer] = None


def get_comparer() -> Comparer:
    """Retrieve or initialize the Comparer singleton instance."""
    global _COMPARER_INSTANCE
    if _COMPARER_INSTANCE is None:
        _COMPARER_INSTANCE = Comparer()
    return _COMPARER_INSTANCE
