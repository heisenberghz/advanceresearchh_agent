"""Researcher workflow component for ResearchOps.

Executes individual research jobs by generating targeted queries, retrieving web sources
via Tavily, and extracting structured facts strictly grounded in source evidence snippets.
Specification: PRD.md Section 6.3/6.4 & TECH_SPEC.md Section 6.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.integrations.openrouter import OpenRouterClient, OpenRouterError, get_openrouter_client
from app.integrations.tavily import TavilyClient, TavilyError, get_tavily_client
from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Evidence, Source

logger = logging.getLogger("researchops.researcher")


class RawFactItem(BaseModel):
    """Raw fact extracted by LLM from source snippets."""

    entity: Optional[str] = Field(default=None, description="The entity being described (e.g. company name)")
    attribute: Optional[str] = Field(default=None, description="The specific attribute or metric (e.g. Founded, Pricing, Revenue)")
    value: str = Field(description="The extracted factual value or claim")
    source_id: str = Field(description="The exact ID of the source supporting this fact")
    evidence_text: str = Field(description="Direct verbatim quote or excerpt from the snippet")


class RawExtractionOutput(BaseModel):
    """Structured container for LLM fact extraction."""

    facts: List[RawFactItem] = Field(
        default_factory=list,
        description="List of extracted facts strictly backed by evidence snippets",
    )


class ResearcherResult(BaseModel):
    """Result of executing an individual research job."""

    job: ResearchJob = Field(description="The executed job with updated status and retry count")
    facts: List[Fact] = Field(default_factory=list, description="Extracted facts with evidence links")
    sources: List[Source] = Field(default_factory=list, description="Retrieved sources cited by facts")
    error: Optional[str] = Field(default=None, description="Error message if research failed")


FACT_EXTRACTION_PROMPT = """You are a meticulous Research Evidence Extractor for "ResearchOps".
Your job is to read search snippets and extract concrete, structured facts about the target entity and attribute.

CRITICAL INVARIANTS:
1. Extract ONLY facts that are explicitly stated in the provided snippets.
2. NEVER guess, extrapolate, or invent values. If information is not in the text, DO NOT include it.
3. Every fact MUST cite the exact `source_id` from which it was extracted.
4. Every fact MUST include the `evidence_text`, which is a verbatim sentence or quote from the snippet supporting the value.
5. If the snippets do not contain relevant facts, return an empty facts list.

Input Format:
Sources will be provided with their IDs and text snippets.
Extract structured facts strictly matching the schema.
"""


from app.workflow.cache import ResearchCache, get_research_cache


class Researcher:
    """Independent researcher unit that executes a single research job."""

    def __init__(
        self,
        tavily_client: Optional[TavilyClient] = None,
        openrouter_client: Optional[OpenRouterClient] = None,
        settings: Optional[Settings] = None,
        cache: Optional[ResearchCache] = None,
    ):
        self.settings = settings or get_settings()
        self.tavily = tavily_client or get_tavily_client()
        self.llm = openrouter_client or get_openrouter_client()
        self.cache = cache or get_research_cache()

    async def execute_job(self, job: ResearchJob) -> ResearcherResult:
        """Execute a single research job with result reuse and caching (Task 36).

        Args:
            job: The ResearchJob to execute.

        Returns:
            ResearcherResult containing updated job, extracted facts, and cited sources.
        """
        job.attempts += 1
        job.updated_at = datetime.now(timezone.utc)
        job.status = JobStatus.RUNNING

        logger.info("Executing ResearchJob %s (Attempt %d): %s", job.id, job.attempts, job.description)

        # 0. Check result reuse cache (Task 36)
        if job.entity and job.attribute:
            reusable = self.cache.get_reusable_results(
                job.entity, job.attribute, job.research_run_id, job.id
            )
            if reusable:
                cached_facts, cached_sources = reusable
                job.status = JobStatus.COMPLETED
                job.result_data = {
                    "reused_from_cache": True,
                    "sources_found": len(cached_sources),
                    "sources_cited": len(cached_sources),
                    "facts_extracted": len(cached_facts),
                }
                logger.info(
                    "⚡ Reused cached facts for job %s (%s - %s): %d facts, %d sources",
                    job.id,
                    job.entity,
                    job.attribute,
                    len(cached_facts),
                    len(cached_sources),
                )
                return ResearcherResult(job=job, facts=cached_facts, sources=cached_sources)

        # 1. Formulate targeted search query
        query = self._generate_search_query(job)

        # 2. Retrieve web sources (check query cache first)
        sources = self.cache.get_cached_sources(query, job.research_run_id)
        if sources is None:
            try:
                sources = await self.tavily.search_to_sources(
                    query=query,
                    research_run_id=job.research_run_id,
                    max_results=self.settings.max_searches_per_job,
                )
                if sources:
                    self.cache.set_cached_sources(query, sources)
            except TavilyError as exc:
                logger.warning("Tavily search failed for job %s: %s", job.id, exc)
                job.status = JobStatus.FAILED
                job.error = str(exc)
                return ResearcherResult(job=job, facts=[], sources=[], error=str(exc))
            except Exception as exc:
                logger.error("Unexpected error searching for job %s: %s", job.id, exc, exc_info=True)
                job.status = JobStatus.FAILED
                job.error = str(exc)
                return ResearcherResult(job=job, facts=[], sources=[], error=str(exc))

        if not sources:
            logger.info("No web sources returned for job %s query '%s'", job.id, query)
            job.status = JobStatus.COMPLETED
            job.result_data = {"sources_found": 0, "facts_extracted": 0}
            return ResearcherResult(job=job, facts=[], sources=[])

        # 3. Extract facts grounded in source snippets
        facts = await self._extract_facts(job, sources)

        # Filter sources to keep only those that support extracted facts (or all if few)
        cited_source_ids = {s_id for fact in facts for s_id in fact.source_ids}
        relevant_sources = [s for s in sources if s.id in cited_source_ids or not cited_source_ids]

        # 4. Cache extracted facts for future queries
        if facts and job.entity and job.attribute:
            self.cache.set_reusable_results(job.entity, job.attribute, facts, relevant_sources)

        job.status = JobStatus.COMPLETED
        job.result_data = {
            "sources_found": len(sources),
            "sources_cited": len(relevant_sources),
            "facts_extracted": len(facts),
        }

        logger.info("Completed job %s: extracted %d facts from %d sources", job.id, len(facts), len(relevant_sources))
        return ResearcherResult(job=job, facts=facts, sources=relevant_sources)

    def _generate_search_query(self, job: ResearchJob) -> str:
        """Formulate a concise, high-signal web search query from the job definition."""
        parts = []
        if job.entity:
            parts.append(job.entity)
        if job.attribute:
            parts.append(job.attribute)
        if not parts:
            parts.append(job.description)
        return " ".join(parts).strip()

    async def _extract_facts(self, job: ResearchJob, sources: List[Source]) -> List[Fact]:
        """Extract structured facts strictly citing retrieved sources."""
        # Check if LLM extraction is possible
        if self.llm.is_configured:
            try:
                return await self._extract_with_llm(job, sources)
            except OpenRouterError as exc:
                logger.warning("LLM fact extraction error (%s); falling back to heuristic extractor", exc)
            except Exception as exc:
                logger.error("Unexpected error in LLM extraction: %s", exc, exc_info=True)

        # Deterministic heuristic extraction for testing/unconfigured environments
        return self._heuristic_extract(job, sources)

    async def _extract_with_llm(self, job: ResearchJob, sources: List[Source]) -> List[Fact]:
        """Extract facts using OpenRouter with structured output."""
        # Format sources context for LLM
        context_blocks = []
        source_map = {s.id: s for s in sources}

        for s in sources:
            snippet = s.evidence or s.title or ""
            context_blocks.append(
                f"[Source ID: {s.id}]\nTitle: {s.title or 'Unknown'}\nURL: {s.url}\nExcerpt: {snippet}"
            )
        context_str = "\n\n".join(context_blocks)

        user_content = (
            f"Research Target:\n"
            f"Entity: {job.entity or 'Unknown'}\n"
            f"Attribute: {job.attribute or 'General Overview'}\n"
            f"Goal: {job.description}\n\n"
            f"Available Evidence Snippets:\n{context_str}\n\n"
            f"Extract all facts found in the snippets for this target."
        )

        messages = [
            {"role": "system", "content": FACT_EXTRACTION_PROMPT},
            {"role": "user", "content": user_content},
        ]

        raw_output = await self.llm.chat_structured(
            messages=messages,
            response_model=RawExtractionOutput,
            model=self.llm.research_model,
            temperature=0.1,
        )

        facts: List[Fact] = []
        now = datetime.now(timezone.utc)

        for idx, item in enumerate(raw_output.facts, start=1):
            # Provenance guard: ensure cited source exists in retrieved set
            cited_source = source_map.get(item.source_id)
            if not cited_source and item.source_id:
                # Try matching by ID substring or domain
                for s in sources:
                    if s.id in item.source_id or item.source_id in s.id or (s.domain and s.domain in item.source_id):
                        cited_source = s
                        break
            if not cited_source and len(sources) == 1:
                cited_source = sources[0]
            if not cited_source:
                continue

            # Ensure evidence text exists
            evidence_str = item.evidence_text.strip() if item.evidence_text else cited_source.evidence or ""
            if not evidence_str:
                continue

            fact_id = f"fact-{job.id}-{idx:02d}"
            evidence = Evidence(
                source_id=cited_source.id,
                text=evidence_str,
                relevance=f"Supports {item.attribute}",
            )

            facts.append(
                Fact(
                    id=fact_id,
                    research_run_id=job.research_run_id,
                    entity=(item.entity.strip() if item.entity else "") or (job.entity or "Unknown"),
                    attribute=(item.attribute.strip() if item.attribute else "") or (job.attribute or "Overview"),
                    value=item.value.strip(),
                    source_ids=[cited_source.id],
                    evidence=[evidence],
                    published_at=cited_source.published_at,
                    retrieved_at=now,
                    trust_tag=TrustTag.RED,  # Unverified until Checker evaluates
                    verification_status=VerificationStatus.UNSUPPORTED,
                )
            )

        return facts

    def _heuristic_extract(self, job: ResearchJob, sources: List[Source]) -> List[Fact]:
        """Deterministic rule-based fact extraction for test environments."""
        facts: List[Fact] = []
        now = datetime.now(timezone.utc)

        for idx, source in enumerate(sources, start=1):
            content = source.evidence or source.title or ""
            if not content:
                continue

            fact_id = f"fact-{job.id}-{idx:02d}"
            entity = job.entity or "Market"
            attribute = job.attribute or "Overview"

            evidence = Evidence(
                source_id=source.id,
                text=content[:250],
                location="Snippet",
            )

            facts.append(
                Fact(
                    id=fact_id,
                    research_run_id=job.research_run_id,
                    entity=entity,
                    attribute=attribute,
                    value=content[:100],
                    source_ids=[source.id],
                    evidence=[evidence],
                    published_at=source.published_at,
                    retrieved_at=now,
                    trust_tag=TrustTag.RED,
                    verification_status=VerificationStatus.UNSUPPORTED,
                )
            )

        return facts


def get_researcher() -> Researcher:
    """Dependency provider for Researcher."""
    return Researcher()
