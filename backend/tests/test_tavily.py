"""Unit tests for Tavily search API integration client."""

from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.integrations.tavily import TavilyClient, TavilyError, TavilySearchResult
from app.models.source import Source


@pytest.mark.anyio
async def test_unconfigured_tavily_raises_error():
    """Verify that calling Tavily without an API key raises a clear TavilyError."""
    with patch("app.integrations.tavily.get_settings") as mock_settings:
        mock_settings.return_value.tavily_api_key = ""
        mock_settings.return_value.max_searches_per_job = 3
        client = TavilyClient(api_key="")
        assert not client.is_configured

        with pytest.raises(TavilyError) as exc_info:
            await client.search(query="Indian CRM market")
        assert "TAVILY_API_KEY is not configured" in str(exc_info.value)


@pytest.mark.anyio
async def test_empty_query_raises_error():
    """Verify empty or blank search query is rejected."""
    client = TavilyClient(api_key="tvly-mock-key")
    with pytest.raises(TavilyError) as exc_info:
        await client.search(query="   ")
    assert "query cannot be empty" in str(exc_info.value)


@pytest.mark.anyio
async def test_successful_search_and_normalization():
    """Verify search returns normalized TavilySearchResult items with clean domains."""
    client = TavilyClient(api_key="tvly-mock-key")

    mock_payload = {
        "query": "Zoho CRM India market share",
        "results": [
            {
                "title": "Zoho CRM Market Report 2026",
                "url": "https://techcrunch.com/2026/01/zoho-report",
                "content": "Zoho reached 100M users with strong adoption in India.",
                "score": 0.94,
                "published_date": "2026-01-15T10:00:00Z",
            },
            {
                "title": "Top Enterprise CRMs",
                "url": "https://www.gartner.com/reviews/market/crm-lead-management",
                "content": "Gartner Magic Quadrant places leading CRM vendors.",
                "score": 0.88,
            },
        ],
    }

    mock_response = httpx.Response(
        status_code=200,
        json=mock_payload,
        request=httpx.Request("POST", "https://api.tavily.com/search"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        results = await client.search("Zoho CRM India market share", max_results=2)

        assert len(results) == 2
        assert isinstance(results[0], TavilySearchResult)
        assert results[0].domain == "techcrunch.com"
        assert results[0].title == "Zoho CRM Market Report 2026"
        assert results[0].score == 0.94
        assert results[1].domain == "www.gartner.com"

        # Verify outgoing request payload
        sent_json = mock_post.call_args.kwargs["json"]
        assert sent_json["query"] == "Zoho CRM India market share"
        assert sent_json["max_results"] == 2
        assert sent_json["api_key"] == "tvly-mock-key"


@pytest.mark.anyio
async def test_search_to_sources_conversion():
    """Verify search_to_sources maps directly to domain Source models with provenance."""
    client = TavilyClient(api_key="tvly-mock-key")

    mock_payload = {
        "results": [
            {
                "title": "Forbes: SaaS in India",
                "url": "https://forbes.com/business/indian-saas",
                "content": "Enterprise SaaS in India grew by 25% year over year.",
                "published_date": "2026-02-01T12:00:00Z",
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=mock_payload,
        request=httpx.Request("POST", "https://api.tavily.com/search"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        sources = await client.search_to_sources(
            query="Indian SaaS revenue",
            research_run_id="run-test-99",
        )

        assert len(sources) == 1
        source = sources[0]
        assert isinstance(source, Source)
        assert source.research_run_id == "run-test-99"
        assert source.url == "https://forbes.com/business/indian-saas"
        assert source.domain == "forbes.com"
        assert "Enterprise SaaS in India" in source.evidence
        assert source.published_at is not None


@pytest.mark.anyio
async def test_tavily_http_error_handling():
    """Verify HTTP errors (e.g. 401 unauthorized or 429 quota) are wrapped in TavilyError."""
    client = TavilyClient(api_key="tvly-mock-key")

    mock_response = httpx.Response(
        status_code=401,
        text="Unauthorized: Invalid API key",
        request=httpx.Request("POST", "https://api.tavily.com/search"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(TavilyError) as exc_info:
            await client.search("CRM pricing")
        assert "Tavily HTTP error 401" in str(exc_info.value)


@pytest.mark.anyio
async def test_tavily_timeout_handling():
    """Verify request timeouts are safely wrapped in TavilyError."""
    client = TavilyClient(api_key="tvly-mock-key", timeout_seconds=1.0)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(TavilyError) as exc_info:
            await client.search("CRM pricing")
        assert "timed out" in str(exc_info.value)
