"""Research Retry Loop Coordinator for ResearchOps.

Specification: PRD.md Section 5, TECH_SPEC.md Section 16, AGENT_TASKS.md Task 16.
Enables bounded conditional re-research when initial research produces
weak, ungrounded, or failing evidence.
Invariant: Strict loop termination, monotonic retry counters, selective re-research,
and zero data loss for previously verified facts.
"""

from copy import deepcopy
import logging
from typing import Dict, List, Optional, Set, Tuple

from app.config import get_settings
from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Source
from app.workflow.parallel import ParallelResearchBatchResult, ParallelResearcher, get_parallel_researcher
from app.workflow.state import ResearchState

logger = logging.getLogger("researchops.retry")

# Targeted search modifiers for retry attempts
RETRY_QUERY_MODIFIERS: List[str] = [
    "official pricing overview cost details",
    "annual report financial filing metrics",
    "comprehensive breakdown specification",
]


class RetryCoordinator:
    """Coordinates selective, bounded re-research for jobs with insufficient evidence."""

    def __init__(
        self,
        parallel_researcher: Optional[ParallelResearcher] = None,
        max_retries: Optional[int] = None,
    ):
        settings = get_settings()
        self.parallel_researcher = parallel_researcher or get_parallel_researcher()
        self.max_retries = max_retries if max_retries is not None else settings.max_research_retries

    def identify_retry_candidates(
        self,
        state: ResearchState,
    ) -> List[ResearchJob]:
        """Identify only jobs whose evidence is missing, ungrounded, or failed, and under retry limit."""
        jobs = state.get("research_jobs", [])
        facts = state.get("facts", [])
        retry_counts = state.get("retry_counts", {})

        # Map entity/attribute to whether they produced at least one verified or yellow fact
        substantiated_pairs: Set[Tuple[str, str]] = set()
        for f in facts:
            f_ent = (f.entity or "").strip().lower()
            f_att = (f.attribute or "").strip().lower()
            if f.trust_tag in (TrustTag.GREEN, TrustTag.YELLOW) and f.verification_status != VerificationStatus.UNSUPPORTED:
                substantiated_pairs.add((f_ent, f_att))

        candidates: List[ResearchJob] = []
        for job in jobs:
            current_attempts = retry_counts.get(job.id, 0)
            if current_attempts >= self.max_retries:
                continue

            job_ent = (job.entity or "").strip().lower()

            # A job needs retry if:
            # 1. It explicitly failed or needs retry
            # 2. Or it has not produced any substantiated fact for its entity
            needs_retry = False
            if job.status in (JobStatus.NEEDS_RETRY, JobStatus.FAILED):
                needs_retry = True
            elif not any((f.entity or "").strip().lower() == job_ent for f in facts if job_ent):
                needs_retry = True
            else:
                # Check facts produced for this specific entity
                entity_facts = [f for f in facts if (f.entity or "").strip().lower() == job_ent]
                if all(f.trust_tag == TrustTag.RED or f.verification_status == VerificationStatus.UNSUPPORTED for f in entity_facts):
                    needs_retry = True

            if needs_retry:
                candidates.append(job)

        return candidates


    def prepare_retry_job(self, job: ResearchJob, attempt: int) -> ResearchJob:
        """Create a targeted variant of the job with refined query scope and incremented attempts."""
        job_copy = deepcopy(job)
        job_copy.attempts = attempt + 1
        job_copy.status = JobStatus.RUNNING

        # Append query modifier to help search engines break out of dead ends
        modifier_idx = min(attempt, len(RETRY_QUERY_MODIFIERS) - 1)
        modifier = RETRY_QUERY_MODIFIERS[modifier_idx]

        original_desc = job_copy.description
        if modifier not in original_desc:
            job_copy.description = f"{original_desc} {modifier}".strip()

        return job_copy

    async def execute_retries(
        self,
        jobs_to_retry: List[ResearchJob],
        current_retry_counts: Dict[str, int],
    ) -> Tuple[ParallelResearchBatchResult, Dict[str, int]]:
        """Execute selected retry jobs concurrently and update retry counters."""
        updated_retry_counts = dict(current_retry_counts)
        prepared_jobs: List[ResearchJob] = []

        for job in jobs_to_retry:
            curr_attempts = updated_retry_counts.get(job.id, 0)
            new_attempts = curr_attempts + 1
            updated_retry_counts[job.id] = new_attempts

            prepared = self.prepare_retry_job(job, curr_attempts)
            prepared_jobs.append(prepared)
            logger.info(
                "Triggering retry attempt %d/%d for job %s (%s - %s)",
                new_attempts,
                self.max_retries,
                job.id,
                job.entity,
                job.description,
            )

        batch_result = await self.parallel_researcher.execute_jobs(prepared_jobs)
        return batch_result, updated_retry_counts

    def should_retry(self, state: ResearchState) -> bool:
        """Deterministic predicate deciding whether to loop back to retry research."""
        candidates = self.identify_retry_candidates(state)
        return len(candidates) > 0


def get_retry_coordinator(
    parallel_researcher: Optional[ParallelResearcher] = None,
    max_retries: Optional[int] = None,
) -> RetryCoordinator:
    """Factory creating default RetryCoordinator instance."""
    return RetryCoordinator(
        parallel_researcher=parallel_researcher,
        max_retries=max_retries,
    )
