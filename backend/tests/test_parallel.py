"""Unit tests for the Parallel Research coordinator."""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.models.enums import JobStatus, TrustTag
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.parallel import ParallelResearchBatchResult, ParallelResearcher
from app.workflow.researcher import Researcher, ResearcherResult


@pytest.fixture
def sample_jobs():
    """Create a list of independent research jobs."""
    return [
        ResearchJob(
            id="job-01",
            research_run_id="run-p1",
            description="Research Zoho CRM founding year",
            entity="Zoho",
            attribute="Founded",
            status=JobStatus.PENDING,
        ),
        ResearchJob(
            id="job-02",
            research_run_id="run-p1",
            description="Research Freshworks CRM founding year",
            entity="Freshworks",
            attribute="Founded",
            status=JobStatus.PENDING,
        ),
        ResearchJob(
            id="job-03",
            research_run_id="run-p1",
            description="Research Salesforce CRM founding year",
            entity="Salesforce",
            attribute="Founded",
            status=JobStatus.PENDING,
        ),
    ]


@pytest.mark.anyio
async def test_parallel_research_empty_batch():
    """Verify executing empty job list returns empty batch result without error."""
    coordinator = ParallelResearcher()
    result = await coordinator.execute_jobs([])
    assert isinstance(result, ParallelResearchBatchResult)
    assert len(result.jobs) == 0
    assert result.completed_count == 0
    assert result.failed_count == 0


@pytest.mark.anyio
async def test_parallel_research_concurrent_execution(sample_jobs):
    """Verify multiple independent research jobs execute concurrently and merge results."""
    mock_researcher = Researcher()

    async def mock_execute(job: ResearchJob) -> ResearcherResult:
        await asyncio.sleep(0.05)  # Simulate non-blocking async network I/O
        job.status = JobStatus.COMPLETED
        job.attempts = 1

        src = Source(
            id=f"src-{job.entity.lower()}",
            research_run_id=job.research_run_id,
            url=f"https://{job.entity.lower()}.com/about",
            title=f"{job.entity} Overview",
            domain=f"{job.entity.lower()}.com",
            evidence=f"{job.entity} was established in year X.",
        )
        fact = Fact(
            id=f"fact-{job.id}-01",
            research_run_id=job.research_run_id,
            entity=job.entity,
            attribute="Founded",
            value="1999",
            source_ids=[src.id],
            evidence=[Evidence(source_id=src.id, text=src.evidence)],
            trust_tag=TrustTag.RED,
        )
        return ResearcherResult(job=job, facts=[fact], sources=[src])

    with patch.object(mock_researcher, "execute_job", side_effect=mock_execute):
        coordinator = ParallelResearcher(researcher=mock_researcher, max_concurrency=3)
        batch: ParallelResearchBatchResult = await coordinator.execute_jobs(sample_jobs)

        assert batch.completed_count == 3
        assert batch.failed_count == 0
        assert len(batch.jobs) == 3
        assert len(batch.facts) == 3
        assert len(batch.sources) == 3

        # Verify all jobs marked completed
        for j in batch.jobs:
            assert j.status == JobStatus.COMPLETED

        # Verify facts from all 3 entities are merged
        entities_found = {f.entity for f in batch.facts}
        assert entities_found == {"Zoho", "Freshworks", "Salesforce"}


@pytest.mark.anyio
async def test_parallel_research_isolated_failure_does_not_abort_batch(sample_jobs):
    """Verify that a single job failure does not destroy or abort successful jobs."""
    mock_researcher = Researcher()

    async def mock_execute(job: ResearchJob) -> ResearcherResult:
        if job.id == "job-02":
            # Job 2 fails
            job.status = JobStatus.FAILED
            job.error = "Tavily rate limit exceeded"
            return ResearcherResult(job=job, facts=[], sources=[], error=job.error)

        # Jobs 1 and 3 succeed
        job.status = JobStatus.COMPLETED
        job.attempts = 1
        src = Source(
            id=f"src-{job.id}",
            research_run_id=job.research_run_id,
            url=f"https://{job.entity.lower()}.com",
            title=f"{job.entity} Info",
        )
        fact = Fact(
            id=f"fact-{job.id}",
            research_run_id=job.research_run_id,
            entity=job.entity,
            attribute="Founded",
            value="2000",
            source_ids=[src.id],
            evidence=[Evidence(source_id=src.id, text="Founded in 2000.")],
            trust_tag=TrustTag.RED,
        )
        return ResearcherResult(job=job, facts=[fact], sources=[src])

    with patch.object(mock_researcher, "execute_job", side_effect=mock_execute):
        coordinator = ParallelResearcher(researcher=mock_researcher)
        batch: ParallelResearchBatchResult = await coordinator.execute_jobs(sample_jobs)

        # Verification of isolated failure boundary
        assert batch.completed_count == 2
        assert batch.failed_count == 1
        assert len(batch.facts) == 2
        assert len(batch.sources) == 2

        # Job 2 is marked failed with error preserved
        job2 = next(j for j in batch.jobs if j.id == "job-02")
        assert job2.status == JobStatus.FAILED
        assert "rate limit" in job2.error

        # Jobs 1 and 3 succeeded and their facts survived
        surviving_entities = {f.entity for f in batch.facts}
        assert surviving_entities == {"Zoho", "Salesforce"}


@pytest.mark.anyio
async def test_parallel_research_deduplicates_sources_by_url(sample_jobs):
    """Verify that duplicate sources cited across multiple jobs are deduplicated in output."""
    mock_researcher = Researcher()
    shared_url = "https://techcrunch.com/2026/indian-crm-leaders"

    async def mock_execute(job: ResearchJob) -> ResearcherResult:
        job.status = JobStatus.COMPLETED
        # Both jobs cite the exact same URL
        src = Source(
            id=f"src-shared-{job.id}",
            research_run_id=job.research_run_id,
            url=shared_url,
            title="Shared Market Report",
        )
        fact = Fact(
            id=f"fact-{job.id}",
            research_run_id=job.research_run_id,
            entity=job.entity,
            attribute="Overview",
            value="Leader",
            source_ids=[src.id],
            evidence=[Evidence(source_id=src.id, text="Market leader overview.")],
            trust_tag=TrustTag.RED,
        )
        return ResearcherResult(job=job, facts=[fact], sources=[src])

    # Test with 2 jobs citing the same URL
    with patch.object(mock_researcher, "execute_job", side_effect=mock_execute):
        coordinator = ParallelResearcher(researcher=mock_researcher)
        batch = await coordinator.execute_jobs(sample_jobs[:2])

        assert batch.completed_count == 2
        assert len(batch.facts) == 2
        # Sources deduplicated to 1 entry
        assert len(batch.sources) == 1
        assert batch.sources[0].url == shared_url
