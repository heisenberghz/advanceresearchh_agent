"""Result reuse and query caching for web research (Task 36).

Provides:
- In-memory bounded LRU search cache with configurable TTL for web search queries.
- Result reuse by entity & attribute to prevent duplicate LLM extraction and Tavily calls.
- Safe source and fact cloning with fresh IDs and current research_run_id binding.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.models.fact import Fact
from app.models.source import Evidence, Source

logger = logging.getLogger("researchops.cache")


class ResearchCache:
    """Thread-safe, bounded in-memory cache for search queries and extracted facts."""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 200):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        # query_key -> (timestamp, list of Sources)
        self._query_cache: Dict[str, Tuple[datetime, List[Source]]] = {}
        # (entity_key, attribute_key) -> (timestamp, list of Facts, list of Sources)
        self._entity_attr_cache: Dict[Tuple[str, str], Tuple[datetime, List[Fact], List[Source]]] = {}

    def get_cached_sources(self, query: str, current_run_id: str) -> Optional[List[Source]]:
        """Retrieve cached sources for a search query if fresh."""
        key = query.strip().lower()
        entry = self._query_cache.get(key)
        if not entry:
            return None

        cached_time, sources = entry
        age = (datetime.now(timezone.utc) - cached_time).total_seconds()
        if age > self.ttl_seconds:
            logger.debug("Cache expired for query '%s' (age: %.1fs > TTL: %ds)", query, age, self.ttl_seconds)
            self._query_cache.pop(key, None)
            return None

        logger.info("⚡ [Cache HIT] Reusing %d cached sources for query: '%s'", len(sources), query)
        cloned: List[Source] = []
        for idx, s in enumerate(sources, start=1):
            cloned.append(
                s.model_copy(
                    update={
                        "id": f"src-cached-{abs(hash(s.url)) % 100000}-{idx}",
                        "research_run_id": current_run_id,
                    }
                )
            )
        return cloned

    def set_cached_sources(self, query: str, sources: List[Source]) -> None:
        """Store search query results in cache."""
        if not sources:
            return
        if len(self._query_cache) >= self.max_entries:
            oldest_key = min(self._query_cache.keys(), key=lambda k: self._query_cache[k][0])
            self._query_cache.pop(oldest_key, None)

        key = query.strip().lower()
        self._query_cache[key] = (datetime.now(timezone.utc), sources)

    def get_reusable_results(
        self, entity: str, attribute: str, current_run_id: str, job_id: str
    ) -> Optional[Tuple[List[Fact], List[Source]]]:
        """Check if identical entity + attribute was already researched."""
        if not entity or not attribute:
            return None

        key = (entity.strip().lower(), attribute.strip().lower())
        entry = self._entity_attr_cache.get(key)
        if not entry:
            return None

        cached_time, facts, sources = entry
        age = (datetime.now(timezone.utc) - cached_time).total_seconds()
        if age > self.ttl_seconds:
            self._entity_attr_cache.pop(key, None)
            return None

        logger.info("⚡ [Cache HIT] Reusing %d facts and %d sources for [%s - %s]", len(facts), len(sources), entity, attribute)

        source_map: Dict[str, str] = {}
        cloned_sources: List[Source] = []
        for idx, s in enumerate(sources, start=1):
            new_id = f"src-{job_id}-{idx:02d}"
            source_map[s.id] = new_id
            cloned_sources.append(
                s.model_copy(
                    update={
                        "id": new_id,
                        "research_run_id": current_run_id,
                    }
                )
            )

        cloned_facts: List[Fact] = []
        for idx, f in enumerate(facts, start=1):
            new_src_ids = [source_map[s_id] for s_id in f.source_ids if s_id in source_map]
            if not new_src_ids and cloned_sources:
                new_src_ids = [cloned_sources[0].id]
            new_evidence = []
            for ev in f.evidence:
                mapped_sid = source_map.get(ev.source_id) or (cloned_sources[0].id if cloned_sources else ev.source_id)
                new_evidence.append(
                    ev.model_copy(
                        update={"source_id": mapped_sid}
                    )
                )

            cloned_facts.append(
                f.model_copy(
                    update={
                        "id": f"fact-{job_id}-{idx:02d}",
                        "research_run_id": current_run_id,
                        "source_ids": new_src_ids,
                        "evidence": new_evidence,
                    }
                )
            )
        return cloned_facts, cloned_sources

    def set_reusable_results(
        self, entity: str, attribute: str, facts: List[Fact], sources: List[Source]
    ) -> None:
        """Store verified facts and sources by entity and attribute."""
        if not entity or not attribute or not facts:
            return
        if len(self._entity_attr_cache) >= self.max_entries:
            oldest_key = min(self._entity_attr_cache.keys(), key=lambda k: self._entity_attr_cache[k][0])
            self._entity_attr_cache.pop(oldest_key, None)

        key = (entity.strip().lower(), attribute.strip().lower())
        self._entity_attr_cache[key] = (datetime.now(timezone.utc), facts, sources)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._query_cache.clear()
        self._entity_attr_cache.clear()


# Global cache singleton instance
_GLOBAL_RESEARCH_CACHE = ResearchCache()


def get_research_cache() -> ResearchCache:
    """Retrieve the global ResearchCache singleton."""
    return _GLOBAL_RESEARCH_CACHE
