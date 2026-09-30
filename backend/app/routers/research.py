"""Research API endpoints for initiating, monitoring, and retrieving research runs.

Specification: PRD.md Section 6 & TECH_SPEC.md Sections 23-24.
Phase 7: Task 21 (POST /research), Task 22 (GET /research/{id}), Task 23 (GET /research/{id}/report).
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.db.repository import ResearchRepository, get_repository
from app.models.report import ResearchReport
from app.workflow.graph import run_research_pipeline

logger = logging.getLogger("researchops.api.research")

router = APIRouter()

# Active in-flight background tasks tracked to prevent garbage collection
_ACTIVE_TASKS: Dict[str, asyncio.Task] = {}


# =============================================================================
# Request / Response Schemas
# =============================================================================

class CreateResearchRequest(BaseModel):
    """Payload to initiate a new research run."""

    question: str = Field(
        ...,
        min_length=3,
        description="Natural-language business, competitive, or market research question",
        examples=["Compare Linear vs Jira on pricing, speed, and market share"],
    )
    assumptions: Optional[List[str]] = Field(
        default=None,
        description="Optional scoping assumptions or hints for the research planner",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Research question cannot be empty or whitespace only.")
        return stripped


class CreateResearchResponse(BaseModel):
    """Immediate acknowledgement returned upon starting a research run."""

    research_id: str = Field(description="Unique identifier for the initiated research run")
    status: str = Field(description="Initial run status, typically 'running' or 'pending'")
    question: str = Field(description="The research question submitted")
    created_at: str = Field(description="ISO-8601 creation timestamp")


class ResearchRunSummary(BaseModel):
    """High-level summary of a research run."""

    id: str
    question: str
    status: str
    assumptions: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class ResearchStatusResponse(BaseModel):
    """Comprehensive status and inspection output for a research run."""

    id: str
    research_id: str
    question: str
    status: str
    current_workflow_stage: str
    workflow_status: str
    research_jobs: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    has_report: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


# =============================================================================
# Helper Utilities
# =============================================================================

def _serialize_item(item: Any) -> Dict[str, Any]:
    """Convert Pydantic models or dicts to JSON-serializable dictionaries."""
    if hasattr(item, "model_dump"):
        data = item.model_dump()
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
            elif isinstance(v, list):
                data[k] = [_serialize_item(elem) if hasattr(elem, "model_dump") else elem for elem in v]
        return data
    if isinstance(item, dict):
        return {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in item.items()
        }
    return dict(item)


async def _execute_pipeline_task(
    research_id: str,
    question: str,
    repo: ResearchRepository,
) -> None:
    """Execute pipeline in background, logging progress and recording failure if uncaught."""
    try:
        logger.info("[Background] Starting research pipeline for %s: '%s'", research_id, question)
        await run_research_pipeline(
            question=question,
            research_id=research_id,
            repository=repo,
        )
        logger.info("[Background] Finished research pipeline successfully for %s", research_id)
    except Exception as exc:
        logger.error(
            "[Background] Research pipeline error for run %s: %s",
            research_id,
            str(exc),
            exc_info=True,
        )
        try:
            repo.update_research_run(run_id=research_id, status="failed")
            repo.save_state_snapshot(
                research_id,
                {"workflow_status": "failed", "error": str(exc)},
            )
        except Exception:
            pass
    finally:
        _ACTIVE_TASKS.pop(research_id, None)


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "",
    response_model=CreateResearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new research run",
    description="Initiates an autonomous research run for the given question and executes the workflow in the background.",
)
async def start_research(
    payload: CreateResearchRequest,
    sync: bool = Query(
        False,
        description="If true, wait synchronously for completion (primarily for automated testing)",
    ),
    repo: ResearchRepository = Depends(get_repository),
) -> CreateResearchResponse:
    """Create a research run and start the multi-agent research workflow."""
    research_id = f"run-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # Persist initial research run
    repo.create_research_run(
        run_id=research_id,
        question=payload.question,
        assumptions=payload.assumptions or [],
        status="running",
    )
    repo.save_state_snapshot(
        research_id,
        {
            "workflow_status": "planned",
            "question": payload.question,
            "assumptions": payload.assumptions or [],
        },
    )

    if sync:
        # Synchronous execution mode for deterministic integration testing
        await _execute_pipeline_task(research_id, payload.question, repo)
        run_data = repo.get_research_run(research_id) or {}
        return CreateResearchResponse(
            research_id=research_id,
            status=run_data.get("status", "completed"),
            question=payload.question,
            created_at=run_data.get("created_at", now),
        )

    # Launch background task
    task = asyncio.create_task(_execute_pipeline_task(research_id, payload.question, repo))
    _ACTIVE_TASKS[research_id] = task

    return CreateResearchResponse(
        research_id=research_id,
        status="running",
        question=payload.question,
        created_at=now,
    )


@router.get(
    "",
    response_model=List[ResearchRunSummary],
    summary="List all research runs",
    description="Retrieves the list of recent research runs ordered by creation time.",
)
async def list_research(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of runs to return"),
    repo: ResearchRepository = Depends(get_repository),
) -> List[ResearchRunSummary]:
    """List research runs from repository."""
    runs = repo.list_research_runs(limit=limit)
    return [
        ResearchRunSummary(
            id=r.get("id", ""),
            question=r.get("question", ""),
            status=r.get("status", "pending"),
            assumptions=r.get("assumptions") or [],
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
            completed_at=r.get("completed_at"),
        )
        for r in runs
    ]


@router.get(
    "/{research_id}",
    response_model=ResearchStatusResponse,
    summary="Get research run status and findings",
    description="Returns detailed status, current workflow stage, jobs, verified facts, conflicts, and gaps.",
)
async def get_research_status(
    research_id: str,
    repo: ResearchRepository = Depends(get_repository),
) -> ResearchStatusResponse:
    """Retrieve full live status and findings for an active or completed research run."""
    run = repo.get_research_run(research_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' not found.",
        )

    snapshot = repo.get_state_snapshot(research_id) or {}

    # Extract jobs
    jobs = snapshot.get("research_jobs") or repo.get_research_jobs(research_id)
    serialized_jobs = [_serialize_item(j) for j in jobs]

    # Extract facts / findings
    facts = snapshot.get("facts") or repo.get_facts(research_id)
    serialized_facts = [_serialize_item(f) for f in facts]

    # Extract conflicts
    conflicts = snapshot.get("conflicts") or repo.get_conflicts(research_id)
    serialized_conflicts = [_serialize_item(c) for c in conflicts]

    # Extract gaps
    gaps = snapshot.get("gaps") or repo.get_research_gaps(research_id)
    serialized_gaps = [_serialize_item(g) for g in gaps]

    # Check report existence
    has_report = (
        snapshot.get("report") is not None
        or repo.get_report(research_id) is not None
    )

    stage = snapshot.get("workflow_status") or run.get("status", "pending")

    return ResearchStatusResponse(
        id=run["id"],
        research_id=run["id"],
        question=run.get("question", ""),
        status=run.get("status", "pending"),
        current_workflow_stage=stage,
        workflow_status=stage,
        research_jobs=serialized_jobs,
        findings=serialized_facts,
        facts=serialized_facts,
        conflicts=serialized_conflicts,
        gaps=serialized_gaps,
        assumptions=run.get("assumptions") or snapshot.get("assumptions") or [],
        has_report=has_report,
        created_at=run.get("created_at"),
        updated_at=run.get("updated_at"),
        completed_at=run.get("completed_at"),
    )


@router.get(
    "/{research_id}/report",
    summary="Get final synthesized research report",
    description="Returns the comprehensive 8-section research report once completed, including rendered markdown.",
)
async def get_research_report(
    research_id: str,
    repo: ResearchRepository = Depends(get_repository),
) -> Dict[str, Any]:
    """Retrieve the generated research report for a completed run."""
    run = repo.get_research_run(research_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' not found.",
        )

    # Check for report in repo or snapshot
    report_data = repo.get_report(research_id)
    if not report_data:
        snapshot = repo.get_state_snapshot(research_id) or {}
        rep_obj = snapshot.get("report")
        if rep_obj:
            report_data = _serialize_item(rep_obj)

    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for research run '{research_id}' not found or not yet generated.",
        )

    serialized = _serialize_item(report_data)

    # Ensure markdown_content is populated
    if not serialized.get("markdown_content"):
        try:
            rep_instance = ResearchReport.model_validate(report_data)
            serialized["markdown_content"] = rep_instance.to_markdown()
        except Exception:
            pass

    return serialized


@router.get(
    "/{research_id}/export/markdown",
    response_class=PlainTextResponse,
    summary="Export research report as Markdown document",
    description="Downloads the completed research report as formatted GitHub-Flavored Markdown.",
)
async def export_markdown_report(
    research_id: str,
    repo: ResearchRepository = Depends(get_repository),
) -> PlainTextResponse:
    """Export the report as a downloadable .md file."""
    report_dict = await get_research_report(research_id, repo)
    md_content = report_dict.get("markdown_content", "")
    if not md_content:
        try:
            rep_instance = ResearchReport.model_validate(report_dict)
            md_content = rep_instance.to_markdown()
        except Exception:
            md_content = f"# Research Report for {research_id}\n\nNo formatted content available."

    headers = {
        "Content-Disposition": f'attachment; filename="research_report_{research_id}.md"',
        "Content-Type": "text/markdown; charset=utf-8",
    }
    return PlainTextResponse(content=md_content, headers=headers)


@router.get(
    "/{research_id}/stream",
    summary="Stream research progress events via SSE",
    description="Server-Sent Events endpoint streaming live state changes during research execution.",
)
async def stream_research_events(
    research_id: str,
    repo: ResearchRepository = Depends(get_repository),
):
    """Stream live research workflow milestones to frontend clients."""
    run = repo.get_research_run(research_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' not found.",
        )

    async def event_generator():
        last_stage = None
        last_status = None
        last_fact_count = -1

        # Poll internal state every 0.3s
        for _ in range(300):  # Cap stream at 90 seconds to prevent hanging
            current_run = repo.get_research_run(research_id)
            if not current_run:
                break

            snapshot = repo.get_state_snapshot(research_id) or {}
            stage = snapshot.get("workflow_status") or current_run.get("status", "pending")
            status_val = current_run.get("status", "pending")
            facts = snapshot.get("facts") or repo.get_facts(research_id)
            fact_count = len(facts)

            # Emit event when stage, status, or fact count changes
            if stage != last_stage or status_val != last_status or fact_count != last_fact_count:
                last_stage = stage
                last_status = status_val
                last_fact_count = fact_count

                event_payload = {
                    "research_id": research_id,
                    "status": status_val,
                    "stage": stage,
                    "workflow_status": stage,
                    "jobs_count": len(snapshot.get("research_jobs") or repo.get_research_jobs(research_id)),
                    "facts_count": fact_count,
                    "conflicts_count": len(snapshot.get("conflicts") or repo.get_conflicts(research_id)),
                    "gaps_count": len(snapshot.get("gaps") or repo.get_research_gaps(research_id)),
                    "has_report": (snapshot.get("report") is not None or repo.get_report(research_id) is not None),
                }
                yield f"data: {json.dumps(event_payload)}\n\n"

            if status_val in ("completed", "failed"):
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
