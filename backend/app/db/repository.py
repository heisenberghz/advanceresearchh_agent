import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.db.client import DatabaseClient, get_supabase_client

logger = logging.getLogger("researchops.repository")


def _serialize_for_db(record: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all nested values, datetimes, and enums are JSON/Postgres compatible."""
    return json.loads(json.dumps(record, default=str))


class ResearchRepository:
    """Repository handling CRUD operations for research pipeline state.

    Interacts with Supabase when configured, with an in-memory state store
    available for offline testing and local evaluation.
    """

    def __init__(self, db_client: Optional[DatabaseClient] = None):
        self.db = db_client or get_supabase_client()
        # In-memory store fallback for offline/test environments
        self._memory_runs: Dict[str, Dict[str, Any]] = {}
        self._memory_jobs: Dict[str, Dict[str, Any]] = {}
        self._memory_facts: Dict[str, Dict[str, Any]] = {}
        self._memory_sources: Dict[str, Dict[str, Any]] = {}
        self._memory_conflicts: Dict[str, Dict[str, Any]] = {}
        self._memory_gaps: Dict[str, Dict[str, Any]] = {}
        self._memory_reports: Dict[str, Dict[str, Any]] = {}
        self._memory_states: Dict[str, Dict[str, Any]] = {}

    # -------------------------------------------------------------------------
    # Research Runs
    # -------------------------------------------------------------------------

    def create_research_run(
        self,
        run_id: str,
        question: str,
        assumptions: Optional[List[str]] = None,
        status: str = "pending",
    ) -> Dict[str, Any]:
        """Create a new research run record."""
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": run_id,
            "question": question,
            "status": status,
            "assumptions": assumptions or [],
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }

        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("research_runs").insert(_serialize_for_db(record)).execute()
                return res.data[0] if res.data else record
            except Exception as exc:
                logger.error("Failed to insert research run to Supabase: %s", str(exc))
                raise RuntimeError(f"Database error creating research run: {exc}") from exc

        # Fallback to in-memory store
        self._memory_runs[run_id] = record
        return record

    def get_research_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a research run by ID."""
        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("research_runs").select("*").eq("id", run_id).execute()
                return res.data[0] if res.data else None
            except Exception as exc:
                logger.error("Failed to retrieve research run %s: %s", run_id, str(exc))
                raise RuntimeError(f"Database error reading research run: {exc}") from exc

        return self._memory_runs.get(run_id)

    def list_research_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve latest research runs."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("research_runs")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to list research runs: %s", str(exc))
                raise RuntimeError(f"Database error listing research runs: {exc}") from exc

        runs = list(self._memory_runs.values())
        runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return runs[:limit]

    def update_research_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        completed_at: Optional[str] = None,
        assumptions: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update research run status or completion timestamp."""
        updates: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if status is not None:
            updates["status"] = status
        if completed_at is not None:
            updates["completed_at"] = completed_at
        if assumptions is not None:
            updates["assumptions"] = assumptions

        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("research_runs")
                    .update(_serialize_for_db(updates))
                    .eq("id", run_id)
                    .execute()
                )
                return res.data[0] if res.data else None
            except Exception as exc:
                logger.error("Failed to update research run %s: %s", run_id, str(exc))
                raise RuntimeError(f"Database error updating research run: {exc}") from exc

        if run_id in self._memory_runs:
            self._memory_runs[run_id].update(updates)
            return self._memory_runs[run_id]
        return None

    # -------------------------------------------------------------------------
    # Research Jobs
    # -------------------------------------------------------------------------

    def save_research_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a research job."""
        now = datetime.now(timezone.utc).isoformat()
        job_data.setdefault("created_at", now)
        job_data["updated_at"] = now

        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("research_jobs").upsert(_serialize_for_db(job_data)).execute()
                return res.data[0] if res.data else job_data
            except Exception as exc:
                logger.error("Failed to save research job: %s", str(exc))
                raise RuntimeError(f"Database error saving research job: {exc}") from exc

        self._memory_jobs[job_data["id"]] = job_data
        return job_data

    def get_research_jobs(self, research_run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all research jobs for a research run."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("research_jobs")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to retrieve research jobs for %s: %s", research_run_id, str(exc))
                raise RuntimeError(f"Database error reading research jobs: {exc}") from exc

        return [
            j for j in self._memory_jobs.values()
            if j.get("research_run_id") == research_run_id
        ]

    # -------------------------------------------------------------------------
    # Sources & Facts
    # -------------------------------------------------------------------------

    def save_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a source record."""
        source_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("sources").upsert(_serialize_for_db(source_data)).execute()
                return res.data[0] if res.data else source_data
            except Exception as exc:
                logger.error("Failed to save source: %s", str(exc))
                raise RuntimeError(f"Database error saving source: {exc}") from exc

        self._memory_sources[source_data["id"]] = source_data
        return source_data

    def get_sources(self, research_run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all sources for a research run."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("sources")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to retrieve sources for %s: %s", research_run_id, str(exc))
                raise RuntimeError(f"Database error reading sources: {exc}") from exc

        return [
            s for s in self._memory_sources.values()
            if s.get("research_run_id") == research_run_id
        ]

    def save_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a verified fact record."""
        now = datetime.now(timezone.utc).isoformat()
        fact_data.setdefault("created_at", now)
        fact_data["updated_at"] = now

        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("facts").upsert(_serialize_for_db(fact_data)).execute()
                return res.data[0] if res.data else fact_data
            except Exception as exc:
                logger.error("Failed to save fact: %s", str(exc))
                raise RuntimeError(f"Database error saving fact: {exc}") from exc

        self._memory_facts[fact_data["id"]] = fact_data
        return fact_data

    def get_facts(self, research_run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all facts for a research run."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("facts")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to retrieve facts for %s: %s", research_run_id, str(exc))
                raise RuntimeError(f"Database error reading facts: {exc}") from exc

        return [
            f for f in self._memory_facts.values()
            if f.get("research_run_id") == research_run_id
        ]

    # -------------------------------------------------------------------------
    # Conflicts & Gaps
    # -------------------------------------------------------------------------

    def save_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a conflict record."""
        conflict_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("conflicts").upsert(_serialize_for_db(conflict_data)).execute()
                return res.data[0] if res.data else conflict_data
            except Exception as exc:
                logger.error("Failed to save conflict: %s", str(exc))
                raise RuntimeError(f"Database error saving conflict: {exc}") from exc

        self._memory_conflicts[conflict_data["id"]] = conflict_data
        return conflict_data

    def get_conflicts(self, research_run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all conflicts for a research run."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("conflicts")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to retrieve conflicts for %s: %s", research_run_id, str(exc))
                raise RuntimeError(f"Database error reading conflicts: {exc}") from exc

        return [
            c for c in self._memory_conflicts.values()
            if c.get("research_run_id") == research_run_id
        ]

    def save_research_gap(self, gap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a research gap record."""
        gap_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        if self.db.is_connected:
            try:
                res = self.db.raw_client.table("research_gaps").upsert(_serialize_for_db(gap_data)).execute()
                return res.data[0] if res.data else gap_data
            except Exception as exc:
                logger.error("Failed to save research gap: %s", str(exc))
                raise RuntimeError(f"Database error saving research gap: {exc}") from exc

        self._memory_gaps[gap_data["id"]] = gap_data
        return gap_data

    def get_research_gaps(self, research_run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all research gaps for a research run."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("research_gaps")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                return res.data or []
            except Exception as exc:
                logger.error("Failed to retrieve research gaps for %s: %s", research_run_id, str(exc))
                raise RuntimeError(f"Database error reading research gaps: {exc}") from exc

        return [
            gap for gap in self._memory_gaps.values()
            if gap.get("research_run_id") == research_run_id
        ]

    # -------------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------------

    def save_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a final synthesized report."""
        now = datetime.now(timezone.utc).isoformat()
        report_data.setdefault("created_at", now)
        report_data["updated_at"] = now

        if self.db.is_connected:
            try:
                payload = {
                    "id": report_data.get("id"),
                    "research_run_id": report_data.get("research_run_id"),
                    "content": _serialize_for_db(report_data),
                    "created_at": report_data.get("created_at", now),
                    "updated_at": report_data.get("updated_at", now),
                }
                res = self.db.raw_client.table("reports").upsert(_serialize_for_db(payload)).execute()
                self._memory_reports[report_data["id"]] = report_data
                return report_data
            except Exception as exc:
                logger.error("Failed to save report to Supabase: %s", str(exc))

        self._memory_reports[report_data["id"]] = report_data
        return report_data

    def get_report(self, research_run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a report by research run ID."""
        if self.db.is_connected:
            try:
                res = (
                    self.db.raw_client.table("reports")
                    .select("*")
                    .eq("research_run_id", research_run_id)
                    .execute()
                )
                if res.data:
                    row = res.data[0]
                    content = row.get("content") or {}
                    if isinstance(content, dict):
                        content.setdefault("id", row.get("id"))
                        content.setdefault("research_run_id", row.get("research_run_id"))
                        content.setdefault("created_at", row.get("created_at"))
                        content.setdefault("updated_at", row.get("updated_at"))
                        return content
                    return row
            except Exception as exc:
                logger.error("Failed to retrieve report for %s from Supabase: %s", research_run_id, str(exc))

        for report in self._memory_reports.values():
            if report.get("research_run_id") == research_run_id:
                return report
        return None

    # -------------------------------------------------------------------------
    # Pipeline State Snapshots
    # -------------------------------------------------------------------------

    def save_state_snapshot(self, run_id: str, updates: Dict[str, Any]) -> None:
        """Update the in-memory state snapshot for a research run."""
        if run_id not in self._memory_states:
            self._memory_states[run_id] = {}
        self._memory_states[run_id].update(updates)

    def get_state_snapshot(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the state snapshot for a research run if available."""
        return self._memory_states.get(run_id)


_REPOSITORY_INSTANCE: Optional[ResearchRepository] = None


def get_repository() -> ResearchRepository:
    """Retrieve or initialize the ResearchRepository singleton instance."""
    global _REPOSITORY_INSTANCE
    if _REPOSITORY_INSTANCE is None:
        _REPOSITORY_INSTANCE = ResearchRepository()
    return _REPOSITORY_INSTANCE
