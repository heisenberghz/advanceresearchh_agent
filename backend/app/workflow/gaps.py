"""Research Gap Detector module identifying missing, unverified, or unavailable research information.

Specification: PRD.md Section 5.3, TECH_SPEC.md Section 15, and AGENT_TASKS.md Task 17.
Key invariants:
- Never fabricate or guess missing values.
- Explicitly represent missing information as structured ResearchGap objects.
- Gaps are persisted and forwarded to the final report/comparer.
"""

import logging
from typing import List, Optional, Set

from app.db.repository import ResearchRepository, get_repository
from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.workflow.state import ResearchState

logger = logging.getLogger("researchops.gaps")


class GapDetector:
    """Detects and registers unestablished or unverified research topics as explicit ResearchGap records."""

    def __init__(self, repository: Optional[ResearchRepository] = None) -> None:
        self.repository = repository or get_repository()

    def detect_gaps(self, state: ResearchState) -> List[ResearchGap]:
        """Analyze research jobs, facts, and verification results to identify true information gaps.

        A research gap occurs when:
        1. A planned research job produced 0 facts (e.g. empty search results or search errors).
        2. A planned research job failed (status == JobStatus.FAILED).
        3. All facts associated with a requested entity/attribute were rejected or marked UNSUPPORTED / RED,
           and retry limits were reached without obtaining verified evidence.

        A topic is NOT a gap if at least one verified fact (GREEN or YELLOW) exists for it.
        """
        run_id = state.get("research_id", "run-default")
        jobs: List[ResearchJob] = state.get("research_jobs", [])
        facts: List[Fact] = state.get("facts", [])
        retry_counts = state.get("retry_counts", {})

        # Map of (entity_lower, attribute_lower) -> list of facts
        # Also build a set of (entity_lower, attribute_lower) that have at least one GREEN or YELLOW verified fact
        verified_topics: Set[tuple[str, str]] = set()
        topic_facts: dict[tuple[str, str], list[Fact]] = {}

        for fact in facts:
            ent = (fact.entity or "").strip().lower()
            attr = (fact.attribute or "").strip().lower()
            key = (ent, attr)
            topic_facts.setdefault(key, []).append(fact)

            if (
                fact.trust_tag in (TrustTag.GREEN, TrustTag.YELLOW)
                and fact.verification_status != VerificationStatus.UNSUPPORTED
            ):
                verified_topics.add(key)

        gaps: List[ResearchGap] = []
        seen_gaps: Set[str] = set()

        for job in jobs:
            ent = (job.entity or "").strip()
            ent_lower = ent.lower()
            attr = (job.attribute or "").strip()
            attr_lower = attr.lower()
            key = (ent_lower, attr_lower)

            # If verified facts exist for this entity and attribute, it is NOT a gap
            if key in verified_topics:
                continue

            attempts = max(job.attempts, retry_counts.get(job.id, 0), 1)
            requested_info = (
                f"{ent} {attr}".strip()
                if (ent and attr)
                else (job.description or f"Information for {ent or 'entity'}")
            )

            # Determine explicit gap reason
            associated_facts = topic_facts.get(key, [])

            if job.status == JobStatus.FAILED:
                reason = (
                    f"Research execution failed: {job.error or 'Service or network error'} "
                    f"after {attempts} attempt(s)."
                )
            elif not associated_facts:
                reason = f"No sufficiently reliable public information found after {attempts} research attempt(s)."
            else:
                # Facts exist but ALL are unverified / RED / unsupported
                unsupported_reasons = [
                    f.verification_reason for f in associated_facts if f.verification_reason
                ]
                if unsupported_reasons:
                    reason = (
                        f"Information could not be verified from reliable sources: {unsupported_reasons[0]}"
                    )
                else:
                    reason = (
                        f"Extracted claims could not be substantiated with authoritative evidence "
                        f"after {attempts} attempt(s)."
                    )

            gap_id = f"gap-{run_id[:8]}-{job.id}"
            if gap_id not in seen_gaps:
                seen_gaps.add(gap_id)
                gap = ResearchGap(
                    id=gap_id,
                    research_run_id=run_id,
                    requested_information=requested_info,
                    reason=reason,
                    attempts=attempts,
                    status="gap",
                )
                gaps.append(gap)
                logger.info(
                    "[GapDetector] Identified research gap for '%s': %s (attempts: %d)",
                    requested_info,
                    reason,
                    attempts,
                )

        return gaps

    def persist_gaps(self, gaps: List[ResearchGap]) -> List[ResearchGap]:
        """Persist identified research gaps into the database or memory repository."""
        persisted: List[ResearchGap] = []
        for gap in gaps:
            try:
                gap_dict = gap.model_dump()
                gap_dict["created_at"] = gap.created_at.isoformat()
                self.repository.save_research_gap(gap_dict)
                persisted.append(gap)
            except Exception as exc:
                logger.error("Failed to persist research gap %s: %s", gap.id, str(exc))
                persisted.append(gap)
        return persisted


_GAP_DETECTOR_INSTANCE: Optional[GapDetector] = None


def get_gap_detector(repository: Optional[ResearchRepository] = None) -> GapDetector:
    """Retrieve or initialize the GapDetector singleton instance."""
    global _GAP_DETECTOR_INSTANCE
    if _GAP_DETECTOR_INSTANCE is None or repository is not None:
        _GAP_DETECTOR_INSTANCE = GapDetector(repository=repository)
    return _GAP_DETECTOR_INSTANCE
