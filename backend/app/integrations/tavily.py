"""Tavily web search API integration with metadata normalization and error handling."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.models.source import Source

logger = logging.getLogger("researchops.tavily")

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilyError(Exception):
    """Exception raised for Tavily API failures."""


class TavilySearchResult(BaseModel):
    """Normalized search result item from Tavily."""

    title: str = Field(default="", description="Webpage or article title")
    url: str = Field(description="Direct URL to the page")
    content: str = Field(default="", description="Snippet or passage extracted by Tavily")
    domain: str = Field(default="", description="Extracted domain hostname")
    score: Optional[float] = Field(default=None, description="Relevance score from Tavily")
    published_date: Optional[str] = Field(default=None, description="Original publication date string")


class TavilyClient:
    """Async client for executing web searches via Tavily API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_results_default: int = 5,
        timeout_seconds: float = 35.0,
        settings: Optional[Settings] = None,
    ):
        cfg = settings or get_settings()
        self.api_key = api_key or cfg.tavily_api_key
        self.max_results_default = min(max_results_default, cfg.max_searches_per_job * 3)
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Provide or initialize a shared AsyncClient with connection limits."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=15, max_connections=30),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ResearchOps/1.0 (Enterprise Market Intelligence)",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close underlying client session if open."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if Tavily API key is available."""
        return bool(self.api_key and self.api_key.strip())

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[TavilySearchResult]:
        """Execute a web search query on Tavily and return normalized search items.

        Args:
            query: Natural language or keyword search query.
            max_results: Maximum results to return (capped to reasonable limit).
            search_depth: "basic" or "advanced".
            include_domains: Restrict search to specific domains.
            exclude_domains: Exclude specific domains.

        Returns:
            List of normalized TavilySearchResult instances.
        """
        if not self.is_configured:
            raise TavilyError(
                "TAVILY_API_KEY is not configured. "
                "Please configure it in backend/.env before executing web searches."
            )

        clean_query = query.strip()
        if not clean_query:
            raise TavilyError("Search query cannot be empty.")

        limit = max_results or self.max_results_default

        payload = {
            "api_key": self.api_key,
            "query": clean_query,
            "search_depth": search_depth,
            "max_results": limit,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        logger.debug("Executing Tavily search for: '%s' (limit: %d)", clean_query, limit)

        client = await self._get_client()

        for attempt in range(2):
            try:
                response = await client.post(
                    TAVILY_SEARCH_URL,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ResearchOps/1.0",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                raw_results = data.get("results", [])
                normalized: List[TavilySearchResult] = []

                for item in raw_results:
                    raw_url = item.get("url", "").strip()
                    if not raw_url:
                        continue

                    # Extract clean domain
                    try:
                        parsed_domain = urlparse(raw_url).netloc.lower()
                    except Exception:
                        parsed_domain = ""

                    normalized.append(
                        TavilySearchResult(
                            title=item.get("title", "").strip(),
                            url=raw_url,
                            content=item.get("content", "").strip(),
                            domain=parsed_domain,
                            score=item.get("score"),
                            published_date=item.get("published_date"),
                        )
                    )

                logger.debug("Tavily returned %d normalized results for '%s'", len(normalized), clean_query)
                return normalized

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt == 0:
                    logger.warning(
                        "Tavily search attempt 1 failed with network/timeout error (%s); retrying in 1s for: '%s'",
                        exc,
                        clean_query,
                    )
                    await asyncio.sleep(1.0)
                    continue
                logger.error("Tavily search timed out for query '%s': %s", clean_query, str(exc))
                raise TavilyError(f"Tavily search timed out after {self.timeout.read}s") from exc

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                error_body = exc.response.text
                logger.error("Tavily returned HTTP %d for query '%s': %s", status_code, clean_query, error_body)
                raise TavilyError(f"Tavily HTTP error {status_code}: {error_body}") from exc

            except TavilyError:
                raise

            except Exception as exc:
                logger.error("Unexpected error during Tavily search: %s", str(exc))
                raise TavilyError(f"Failed to communicate with Tavily search: {exc}") from exc

    async def search_to_sources(
        self,
        query: str,
        research_run_id: str,
        max_results: Optional[int] = None,
    ) -> List[Source]:
        """Perform search and map results directly into domain Source models with provenance."""
        results = await self.search(query=query, max_results=max_results)
        sources: List[Source] = []
        now = datetime.now(timezone.utc)

        for idx, res in enumerate(results, start=1):
            source_id = f"src-{abs(hash(res.url)) % 10000000:07d}"

            # Try parsing published_date if provided
            published_dt = None
            if res.published_date:
                try:
                    published_dt = datetime.fromisoformat(res.published_date.replace("Z", "+00:00"))
                except Exception:
                    published_dt = None

            sources.append(
                Source(
                    id=source_id,
                    research_run_id=research_run_id,
                    url=res.url,
                    title=res.title,
                    domain=res.domain,
                    published_at=published_dt,
                    retrieved_at=now,
                    evidence=res.content,
                )
            )

        return sources


def get_tavily_client() -> TavilyClient:
    """Dependency provider for TavilyClient."""
    return TavilyClient()
