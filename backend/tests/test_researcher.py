"""Unit tests for the Researcher workflow component."""

from unittest.mock import AsyncMock, patch
import pytest

from app.integrations.openrouter import OpenRouterClient
from app.integrations.tavily import TavilyClient, TavilyError
from app.models.enums import JobStatus, TrustTag
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Source
from app.workflow.researcher import (
    RawExtractionOutput,
    RawFactItem,
    Researcher,
    ResearcherResult,
)


@pytest.fixture
def sample_job():
    """Create a sample research job for testing."""
    return ResearchJob(
        id="job-101",
        research_run_id="run-test-crm",
        description="Research Zoho CRM founding year and headquarters",
        entity="Zoho",
        attribute="Founded & HQ",
        status=JobStatus.PENDING,
    )


@pytest.fixture
def mock_sources():
    """Create sample mock sources returned from Tavily."""
    return [
        Source(
            id="src-0000001",
            research_run_id="run-test-crm",
            url="https://techcrunch.com/zoho-profile",
            title="Zoho Company Profile",
            domain="techcrunch.com",
            evidence="Zoho Corporation was founded in 1996 and is headquartered in Chennai, India.",
        ),
        Source(
            id="src-0000002",
            research_run_id="run-test-crm",
            url="https://forbes.com/zoho-growth",
            title="Forbes on Zoho",
            domain="forbes.com",
            evidence="Sridhar Vembu co-founded Zoho in 1996 in Tamil Nadu.",
        ),
    ]


@pytest.mark.anyio
async def test_researcher_successful_execution_with_llm(sample_job, mock_sources):
    """Verify Researcher executes search, calls LLM, and preserves source provenance."""
    mock_tavily = TavilyClient(api_key="tvly-mock")
    mock_llm = OpenRouterClient(api_key="sk-mock")

    mock_raw_facts = RawExtractionOutput(
        facts=[
            RawFactItem(
                entity="Zoho",
                attribute="Founded",
                value="1996",
                source_id="src-0000001",
                evidence_text="Zoho Corporation was founded in 1996.",
            ),
            RawFactItem(
                entity="Zoho",
                attribute="Headquarters",
                value="Chennai, India",
                source_id="src-0000001",
                evidence_text="headquartered in Chennai, India.",
            ),
        ]
    )

    with patch.object(mock_tavily, "search_to_sources", new_callable=AsyncMock) as mock_search, \
         patch.object(mock_llm, "chat_structured", new_callable=AsyncMock) as mock_chat:

        mock_search.return_value = mock_sources
        mock_chat.return_value = mock_raw_facts

        researcher = Researcher(tavily_client=mock_tavily, openrouter_client=mock_llm)
        result: ResearcherResult = await researcher.execute_job(sample_job)

        assert result.error is None
        assert result.job.status == JobStatus.COMPLETED
        assert result.job.attempts == 1
        assert len(result.facts) == 2

        # Verify fact 1 provenance
        fact1 = result.facts[0]
        assert isinstance(fact1, Fact)
        assert fact1.entity == "Zoho"
        assert fact1.attribute == "Founded"
        assert fact1.value == "1996"
        assert fact1.source_ids == ["src-0000001"]
        assert len(fact1.evidence) == 1
        assert fact1.evidence[0].source_id == "src-0000001"
        assert "1996" in fact1.evidence[0].text
        assert fact1.trust_tag == TrustTag.RED  # Unverified until evaluated by Checker

        # Verify cited sources
        assert len(result.sources) >= 1
        assert result.sources[0].id == "src-0000001"


@pytest.mark.anyio
async def test_researcher_provenance_guard_rejects_hallucinated_sources(sample_job, mock_sources):
    """Verify that facts citing non-existent source IDs are discarded."""
    mock_tavily = TavilyClient(api_key="tvly-mock")
    mock_llm = OpenRouterClient(api_key="sk-mock")

    # LLM hallucinates a source ID "src-fake-999" not in mock_sources
    mock_raw_facts = RawExtractionOutput(
        facts=[
            RawFactItem(
                entity="Zoho",
                attribute="Revenue",
                value="$1 Billion",
                source_id="src-fake-999",
                evidence_text="Invented snippet",
            ),
        ]
    )

    with patch.object(mock_tavily, "search_to_sources", new_callable=AsyncMock) as mock_search, \
         patch.object(mock_llm, "chat_structured", new_callable=AsyncMock) as mock_chat:

        mock_search.return_value = mock_sources
        mock_chat.return_value = mock_raw_facts

        researcher = Researcher(tavily_client=mock_tavily, openrouter_client=mock_llm)
        result = await researcher.execute_job(sample_job)

        # The hallucinated fact should be rejected by the provenance guard
        assert len(result.facts) == 0


@pytest.mark.anyio
async def test_researcher_handles_search_failure_gracefully(sample_job):
    """Verify search network errors mark the job as FAILED without raising unhandled exceptions."""
    mock_tavily = TavilyClient(api_key="tvly-mock")

    with patch.object(mock_tavily, "search_to_sources", side_effect=TavilyError("Tavily quota exceeded")):
        researcher = Researcher(tavily_client=mock_tavily)
        result: ResearcherResult = await researcher.execute_job(sample_job)

        assert result.job.status == JobStatus.FAILED
        assert "quota exceeded" in result.job.error
        assert len(result.facts) == 0


@pytest.mark.anyio
async def test_researcher_handles_empty_search_results(sample_job):
    """Verify job completes cleanly with zero facts when no web sources are found."""
    mock_tavily = TavilyClient(api_key="tvly-mock")

    with patch.object(mock_tavily, "search_to_sources", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []

        researcher = Researcher(tavily_client=mock_tavily)
        result = await researcher.execute_job(sample_job)

        assert result.job.status == JobStatus.COMPLETED
        assert len(result.facts) == 0
        assert len(result.sources) == 0
