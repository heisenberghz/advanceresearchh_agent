"""Unit tests for ResearchCache and result reuse (Task 36)."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.cache import ResearchCache, get_research_cache
from app.workflow.researcher import Researcher


def test_cache_query_sources_hit_and_miss():
    """Verify search queries are cached and returned with cloned IDs."""
    cache = ResearchCache(ttl_seconds=3600)
    sources = [
        Source(
            id="src-1",
            research_run_id="run-initial",
            url="https://linear.app/pricing",
            evidence="Linear standard tier is $8/user/month.",
        )
    ]

    # Miss before setting
    assert cache.get_cached_sources("Linear pricing tiers", "run-new") is None

    # Set cache
    cache.set_cached_sources("Linear pricing tiers", sources)

    # Hit with case-insensitivity
    cached = cache.get_cached_sources("  linear PRICING tiers  ", "run-new")
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].url == "https://linear.app/pricing"
    assert cached[0].research_run_id == "run-new"
    assert cached[0].id != "src-1"  # Cloned ID


def test_cache_expiration_ttl():
    """Verify cached sources expire when older than TTL."""
    cache = ResearchCache(ttl_seconds=10)
    sources = [
        Source(
            id="src-1",
            research_run_id="run-1",
            url="https://jira.com",
            title="Jira",
        )
    ]
    cache.set_cached_sources("Jira speed", sources)

    # Manually backdate the cache entry
    key = "jira speed"
    cache._query_cache[key] = (
        datetime.now(timezone.utc) - timedelta(seconds=20),
        sources,
    )

    assert cache.get_cached_sources("Jira speed", "run-2") is None


def test_cache_bounded_eviction():
    """Verify cache respects max_entries and evicts oldest items."""
    cache = ResearchCache(ttl_seconds=3600, max_entries=2)
    s = [Source(id="s1", research_run_id="r1", url="https://test.com", title="T")]

    cache.set_cached_sources("query 1", s)
    cache.set_cached_sources("query 2", s)
    cache.set_cached_sources("query 3", s)  # Should evict query 1

    assert len(cache._query_cache) == 2
    assert cache.get_cached_sources("query 1", "r2") is None
    assert cache.get_cached_sources("query 2", "r2") is not None
    assert cache.get_cached_sources("query 3", "r2") is not None


def test_entity_attribute_result_reuse():
    """Verify entity and attribute facts are reused and cleanly rebound."""
    cache = ResearchCache(ttl_seconds=3600)
    source = Source(
        id="src-original",
        research_run_id="run-old",
        url="https://linear.app/pricing",
        title="Linear Pricing",
    )
    fact = Fact(
        id="fact-original",
        research_run_id="run-old",
        entity="Linear",
        attribute="Pricing",
        value="$8 per user/mo",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        source_ids=["src-original"],
        evidence=[Evidence(source_id="src-original", text="Standard tier costs $8.")],
    )

    cache.set_reusable_results("Linear", "Pricing", [fact], [source])

    # Reusing for a different research run
    reused = cache.get_reusable_results("linear", "pricing", "run-brand-new", "job-99")
    assert reused is not None
    reused_facts, reused_sources = reused

    assert len(reused_facts) == 1
    assert len(reused_sources) == 1
    assert reused_facts[0].research_run_id == "run-brand-new"
    assert reused_facts[0].id == "fact-job-99-01"
    assert reused_sources[0].id == "src-job-99-01"
    assert reused_facts[0].source_ids == ["src-job-99-01"]
    assert reused_facts[0].evidence[0].source_id == "src-job-99-01"


@pytest.mark.anyio
async def test_researcher_uses_cache_and_skips_tavily():
    """Verify Researcher executes repeated job entirely from cache without calling Tavily."""
    cache = ResearchCache(ttl_seconds=3600)
    mock_tavily = AsyncMock()

    source = Source(
        id="src-1",
        research_run_id="run-1",
        url="https://notion.so/pricing",
        title="Notion Pricing",
        evidence="Free tier available, Plus tier is $10/mo.",
    )
    mock_tavily.search_to_sources.return_value = [source]

    researcher = Researcher(tavily_client=mock_tavily, cache=cache)

    job1 = ResearchJob(
        id="job-1",
        research_run_id="run-1",
        description="Research Notion pricing",
        entity="Notion",
        attribute="Pricing",
        status=JobStatus.PENDING,
    )

    # First execution: calls Tavily
    result1 = await researcher.execute_job(job1)
    assert result1.job.status == JobStatus.COMPLETED
    assert mock_tavily.search_to_sources.call_count == 1
    assert len(result1.facts) >= 1

    # Second execution for a different run: should be served 100% from cache!
    job2 = ResearchJob(
        id="job-2",
        research_run_id="run-2",
        description="Research Notion pricing again",
        entity="Notion",
        attribute="Pricing",
        status=JobStatus.PENDING,
    )

    result2 = await researcher.execute_job(job2)
    assert result2.job.status == JobStatus.COMPLETED
    assert result2.job.result_data.get("reused_from_cache") is True
    # Tavily call count MUST STILL BE 1 (Zero additional API calls made!)
    assert mock_tavily.search_to_sources.call_count == 1
    assert len(result2.facts) == len(result1.facts)
    assert result2.facts[0].research_run_id == "run-2"
