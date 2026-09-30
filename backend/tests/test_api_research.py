"""Tests for Research REST API endpoints (Phase 7: Tasks 21, 22, 23).

Tests:
- POST /research (Start research run)
- GET /research/{id} (Inspect research status, stage, jobs, facts, conflicts, gaps)
- GET /research/{id}/report (Fetch synthesized final report)
- GET /research/{id}/export/markdown (Export report as markdown)
- GET /research (List research runs)
- GET /research/{id}/stream (SSE progress streaming)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.repository import get_repository
from app.models.enums import ConflictStatus, JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.conflict import Conflict, CompetingValue
from app.models.gap import ResearchGap
from app.models.report import ResearchReport
from app.models.source import Evidence, Source


@pytest.fixture
def repo():
    """Get the singleton repository instance and clean state for tests."""
    r = get_repository()
    r._memory_runs.clear()
    r._memory_jobs.clear()
    r._memory_facts.clear()
    r._memory_sources.clear()
    r._memory_conflicts.clear()
    r._memory_gaps.clear()
    r._memory_reports.clear()
    r._memory_states.clear()
    return r


@pytest.fixture
def client(repo):
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# Task 21: POST /research
# =============================================================================

def test_start_research_validation_error(client):
    """Verify POST /research rejects empty or whitespace questions."""
    # Blank string triggers validation error -> 422
    res = client.post("/research", json={"question": "   "})
    assert res.status_code == 422

    # Missing question triggers validation -> 422
    res_missing = client.post("/research", json={})
    assert res_missing.status_code == 422


def test_start_research_success(client, repo):
    """Verify POST /research starts run, returns 201, run ID, and initial status."""
    with patch("app.routers.research.run_research_pipeline", new_callable=AsyncMock) as mock_pipeline:
        payload = {
            "question": "Compare Notion and Obsidian on offline support and pricing",
            "assumptions": ["Focus on desktop and mobile plans"],
        }
        res = client.post("/research", json=payload)
        assert res.status_code == 201
        data = res.json()

        assert "research_id" in data
        assert data["research_id"].startswith("run-")
        assert data["status"] == "running"
        assert data["question"] == payload["question"]
        assert "created_at" in data

        # Verify run was saved to repository
        run_record = repo.get_research_run(data["research_id"])
        assert run_record is not None
        assert run_record["question"] == payload["question"]
        assert run_record["assumptions"] == payload["assumptions"]


def test_list_research_runs(client, repo):
    """Verify GET /research returns list of recent research runs."""
    repo.create_research_run("run-1", "Question 1", status="completed")
    repo.create_research_run("run-2", "Question 2", status="running")

    res = client.get("/research")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    ids = [r["id"] for r in data]
    assert "run-1" in ids
    assert "run-2" in ids


# =============================================================================
# Task 22: GET /research/{id}
# =============================================================================

def test_get_research_status_not_found(client):
    """Verify GET /research/{id} returns 404 for unknown run IDs."""
    res = client.get("/research/nonexistent-run-id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_get_research_status_detailed(client, repo):
    """Verify GET /research/{id} returns complete progress, stage, jobs, facts, conflicts, and gaps."""
    run_id = "run-test-detail"
    repo.create_research_run(
        run_id=run_id,
        question="Compare Datadog and New Relic on pricing",
        status="running",
        assumptions=["Compare Enterprise tiers"],
    )

    # Populate jobs
    job = ResearchJob(
        id="job-1",
        research_run_id=run_id,
        description="Research Datadog pricing",
        entity="Datadog",
        attribute="Pricing",
        status=JobStatus.COMPLETED,
    )
    repo.save_research_job(job.model_dump())

    # Populate verified facts
    fact = Fact(
        id="fact-1",
        research_run_id=run_id,
        entity="Datadog",
        attribute="Pricing",
        value="$15/host/mo",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        verification_reason="Official pricing page",
        source_ids=["src-1"],
        evidence=[Evidence(text="Pro tier starts at $15 per host monthly.", source_id="src-1")],
    )
    repo.save_fact(fact.model_dump())

    # Populate conflict
    conflict = Conflict(
        id="conf-1",
        research_run_id=run_id,
        entity="Datadog",
        attribute="Pricing",
        description="Conflicting pricing claims for Datadog Pro tier.",
        status=ConflictStatus.UNRESOLVED,
        competing_values=[
            CompetingValue(value="$15/host/mo", source_id="src-1", evidence="Official site"),
            CompetingValue(value="$23/host/mo", source_id="src-2", evidence="Industry article"),
        ],
        supporting_sources=["src-1", "src-2"],
        resolution_note="Preserved both claims with source context",
    )
    repo.save_conflict(conflict.model_dump())

    # Populate gap
    gap = ResearchGap(
        id="gap-1",
        research_run_id=run_id,
        requested_information="New Relic: Enterprise Volume Discount",
        reason="Information not publicly disclosed",
        attempts=2,
    )
    repo.save_research_gap(gap.model_dump())

    # Set state snapshot
    repo.save_state_snapshot(run_id, {
        "workflow_status": "checked",
        "research_jobs": [job.model_dump()],
        "facts": [fact.model_dump()],
        "conflicts": [conflict.model_dump()],
        "gaps": [gap.model_dump()],
    })

    res = client.get(f"/research/{run_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == run_id
    assert data["research_id"] == run_id
    assert data["status"] == "running"
    assert data["current_workflow_stage"] == "checked"
    assert data["workflow_status"] == "checked"

    # Verify jobs
    assert len(data["research_jobs"]) == 1
    assert data["research_jobs"][0]["id"] == "job-1"

    # Verify findings / facts
    assert len(data["findings"]) == 1
    assert data["findings"][0]["entity"] == "Datadog"
    assert data["findings"][0]["trust_tag"] == "GREEN"

    # Verify conflicts
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["id"] == "conf-1"

    # Verify gaps
    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["requested_information"] == "New Relic: Enterprise Volume Discount"

    # Report presence
    assert data["has_report"] is False


# =============================================================================
# Task 23: GET /research/{id}/report
# =============================================================================

def test_get_research_report_not_found(client, repo):
    """Verify GET /research/{id}/report returns 404 when run or report is missing."""
    # Unknown run ID
    res = client.get("/research/nonexistent/report")
    assert res.status_code == 404

    # Run exists but report not yet generated
    repo.create_research_run("run-no-rep", "Question", status="running")
    res_pending = client.get("/research/run-no-rep/report")
    assert res_pending.status_code == 404
    assert "not found or not yet generated" in res_pending.json()["detail"].lower()


def test_get_research_report_success(client, repo):
    """Verify GET /research/{id}/report returns full structured report with markdown."""
    run_id = "run-with-report"
    repo.create_research_run(run_id, "Compare A vs B", status="completed")

    report = ResearchReport(
        id="rep-1",
        research_run_id=run_id,
        title="Comparative Analysis: A vs B",
        executive_summary="Company A leads on cost while Company B offers greater scalability.",
        assumptions=["Focus on 2026 pricing"],
        key_findings=["Finding 1: A costs 30% less.", "Finding 2: B has 99.99% uptime."],
        markdown_content="# Comparative Analysis: A vs B\n\n## 1. Executive Summary\nCompany A leads on cost.",
    )
    repo.save_report(report.model_dump())
    repo.save_state_snapshot(run_id, {"workflow_status": "completed", "report": report})

    res = client.get(f"/research/{run_id}/report")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == "rep-1"
    assert data["research_run_id"] == run_id
    assert data["title"] == "Comparative Analysis: A vs B"
    assert "Company A leads on cost" in data["executive_summary"]
    assert len(data["key_findings"]) == 2
    assert "markdown_content" in data
    assert "# Comparative Analysis: A vs B" in data["markdown_content"]


def test_export_markdown_report(client, repo):
    """Verify GET /research/{id}/export/markdown returns downloadable markdown file."""
    run_id = "run-export-md"
    repo.create_research_run(run_id, "Question", status="completed")

    report = ResearchReport(
        id="rep-export",
        research_run_id=run_id,
        title="Export Test Report",
        executive_summary="Testing Markdown export endpoint.",
        markdown_content="# Export Test Report\n\nExecutive summary content.",
    )
    repo.save_report(report.model_dump())

    res = client.get(f"/research/{run_id}/export/markdown")
    assert res.status_code == 200
    assert "text/markdown" in res.headers["content-type"]
    assert "attachment" in res.headers["content-disposition"]
    assert f"research_report_{run_id}.md" in res.headers["content-disposition"]
    assert "# Export Test Report" in res.text


# =============================================================================
# Streaming progress via SSE (GET /research/{id}/stream)
# =============================================================================

def test_stream_research_events(client, repo):
    """Verify GET /research/{id}/stream produces SSE events matching run state."""
    run_id = "run-stream-test"
    repo.create_research_run(run_id, "Stream question", status="completed")
    repo.save_state_snapshot(run_id, {"workflow_status": "completed"})

    res = client.get(f"/research/{run_id}/stream")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    # Read SSE text
    stream_content = res.text
    assert "data: " in stream_content
    assert run_id in stream_content
    assert "completed" in stream_content


def test_start_research_sync_e2e(client, repo):
    """Verify POST /research?sync=true runs pipeline synchronously to completion."""
    async def mock_search(query, research_run_id, max_results=None):
        return [
            Source(
                id=f"src-{abs(hash(query)) % 1000}",
                research_run_id=research_run_id,
                url="https://zoho.com/pricing",
                title="Zoho Pricing",
                raw_content="Zoho CRM standard tier is $14 per user monthly.",
            )
        ]

    with patch("app.integrations.tavily.TavilyClient.search", side_effect=mock_search):
        res = client.post(
            "/research?sync=true",
            json={"question": "What is the pricing model of Zoho?"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "completed"
        run_id = data["research_id"]

        # Check status endpoint
        res_status = client.get(f"/research/{run_id}")
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert status_data["status"] == "completed"
        assert status_data["workflow_status"] == "completed"
        assert status_data["has_report"] is True

        # Check report endpoint
        res_report = client.get(f"/research/{run_id}/report")
        assert res_report.status_code == 200
        report_data = res_report.json()
        assert "markdown_content" in report_data
        assert report_data["research_run_id"] == run_id

