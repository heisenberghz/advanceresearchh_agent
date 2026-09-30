"""Parallel Research execution coordinator for ResearchOps.

Executes multiple independent ResearchJobs concurrently with bounded concurrency
and isolated failure boundaries.
Specification: PRD.md Section 6.3 & TECH_SPEC.md Section 19.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.enums import JobStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Source
from app.workflow.researcher import Researcher, ResearcherResult, get_researcher

logger = logging.getLogger("researchops.parallel")


class ParallelResearchBatchResult(BaseModel):
    """Aggregated output from running a batch of research jobs concurrently."""

    jobs: List[ResearchJob] = Field(description="All jobs with updated statuses")
    facts: List[Fact] = Field(default_factory=list, description="Aggregated facts across all successful jobs")
    sources: List[Source] = Field(default_factory=list, description="Deduplicated sources cited across jobs")
    completed_count: int = Field(default=0, description="Number of successfully completed jobs")
    failed_count: int = Field(default=0, description="Number of failed jobs")


class ParallelResearcher:
    """Coordinator that dispatches and gathers concurrent research tasks."""

    def __init__(
        self,
        researcher: Optional[Researcher] = None,
        max_concurrency: int = 4,
    ):
        self.researcher = researcher or get_researcher()
        self.max_concurrency = max(1, max_concurrency)

    async def execute_jobs(self, jobs: List[ResearchJob]) -> ParallelResearchBatchResult:
        """Run a list of research jobs in parallel with isolated error boundaries.

        Args:
            jobs: List of ResearchJob instances to execute.

        Returns:
            ParallelResearchBatchResult containing merged facts, deduplicated sources,
            and updated job statuses.
        """
        if not jobs:
            return ParallelResearchBatchResult(jobs=[])

        logger.info("Starting parallel execution of %d research jobs (concurrency limit: %d)",
                    len(jobs), self.max_concurrency)

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _run_single_job(job: ResearchJob) -> ResearcherResult:
            async with semaphore:
                try:
                    return await self.researcher.execute_job(job)
                except Exception as exc:
                    logger.error("Unhandled exception in parallel worker for job %s: %s", job.id, exc, exc_info=True)
                    job.status = JobStatus.FAILED
                    job.error = f"Worker exception: {exc}"
                    return ResearcherResult(job=job, facts=[], sources=[], error=str(exc))

        # Launch all tasks concurrently with isolated exception safety
        tasks = [_run_single_job(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs: List[ResearchJob] = []
        all_facts: List[Fact] = []
        sources_by_url: Dict[str, Source] = {}
        sources_by_id: Dict[str, Source] = {}
        completed_count = 0
        failed_count = 0

        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("Job task %d raised unexpected exception: %s", idx, res)
                failed_job = jobs[idx]
                failed_job.status = JobStatus.FAILED
                failed_job.error = str(res)
                all_jobs.append(failed_job)
                failed_count += 1
                continue

            # Standard ResearcherResult
            all_jobs.append(res.job)

            if res.job.status == JobStatus.COMPLETED:
                completed_count += 1
                all_facts.extend(res.facts)

                # Deduplicate sources by URL while preserving unique IDs
                for src in res.sources:
                    if src.url not in sources_by_url:
                        sources_by_url[src.url] = src
                        sources_by_id[src.id] = src
            else:
                failed_count += 1
                logger.warning("Job %s did not complete successfully (status: %s, error: %s)",
                               res.job.id, res.job.status, res.error)

        deduplicated_sources = list(sources_by_url.values())

        logger.info(
            "Parallel batch completed: %d succeeded, %d failed | Collected %d facts, %d unique sources",
            completed_count, failed_count, len(all_facts), len(deduplicated_sources)
        )

        return ParallelResearchBatchResult(
            jobs=all_jobs,
            facts=all_facts,
            sources=deduplicated_sources,
            completed_count=completed_count,
            failed_count=failed_count,
        )


def get_parallel_researcher() -> ParallelResearcher:
    """Dependency provider for ParallelResearcher."""
    return ParallelResearcher()
