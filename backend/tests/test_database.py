"""Tests for database schema, client, and persistence repository."""

from pathlib import Path
import pytest
from app.db.client import DatabaseClient, get_supabase_client
from app.db.repository import ResearchRepository


def test_schema_file_completeness():
    """Verify that schema.sql contains all 7 core tables specified in TECH_SPEC.md."""
    schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    assert schema_path.exists(), "schema.sql file is missing"

    content = schema_path.read_text(encoding="utf-8")

    expected_tables = [
        "research_runs",
        "research_jobs",
        "sources",
        "facts",
        "conflicts",
        "research_gaps",
        "reports",
    ]

    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in content, f"Table {table} missing in schema.sql"


def test_supabase_client_unconfigured_behavior():
    """Verify DatabaseClient behaves safely when unconfigured."""
    client = DatabaseClient(None)
    assert not client.is_connected
    ping_result = client.ping()
    assert ping_result["connected"] is False
    assert "not configured" in ping_result["reason"].lower()

    with pytest.raises(RuntimeError) as exc_info:
        _ = client.raw_client
    assert "not configured" in str(exc_info.value)


def test_repository_crud_operations():
    """Verify ResearchRepository correctly performs CRUD operations."""
    repo = ResearchRepository(DatabaseClient(None))

    # 1. Create run
    run = repo.create_research_run(
        run_id="test-run-123",
        question="Compare major CRM competitors in India",
        assumptions=["Focus on enterprise market", "Public metrics only"],
    )
    assert run["id"] == "test-run-123"
    assert run["status"] == "pending"
    assert len(run["assumptions"]) == 2

    # 2. Get run
    retrieved = repo.get_research_run("test-run-123")
    assert retrieved is not None
    assert retrieved["question"] == "Compare major CRM competitors in India"

    # 3. Update run
    updated = repo.update_research_run("test-run-123", status="running")
    assert updated["status"] == "running"

    # 4. Save job
    job = repo.save_research_job({
        "id": "job-1",
        "research_run_id": "test-run-123",
        "description": "Identify Indian CRM competitors",
        "entity": "CRM Market",
        "status": "completed",
    })
    assert job["id"] == "job-1"

    # 5. Save source
    source = repo.save_source({
        "id": "src-1",
        "research_run_id": "test-run-123",
        "url": "https://example.com/crm-report",
        "title": "CRM Market Analysis 2026",
        "domain": "example.com",
    })
    assert source["id"] == "src-1"

    # 6. Save fact
    fact = repo.save_fact({
        "id": "fact-1",
        "research_run_id": "test-run-123",
        "entity": "Zoho",
        "attribute": "Founded",
        "value": "1996",
        "trust_tag": "GREEN",
        "verification_status": "verified",
        "source_ids": ["src-1"],
    })
    assert fact["id"] == "fact-1"
    assert fact["trust_tag"] == "GREEN"

    # 7. Save conflict
    conflict = repo.save_conflict({
        "id": "conflict-1",
        "research_run_id": "test-run-123",
        "description": "Discrepancy in reported annual revenue for Company X",
        "status": "unresolved",
        "competing_values": [{"source": "A", "val": "100 Cr"}, {"source": "B", "val": "130 Cr"}],
    })
    assert conflict["id"] == "conflict-1"

    # 8. Save research gap
    gap = repo.save_research_gap({
        "id": "gap-1",
        "research_run_id": "test-run-123",
        "requested_information": "Enterprise custom pricing for Company Y",
        "reason": "Custom quote required, no public disclosures found",
        "attempts": 2,
    })
    assert gap["id"] == "gap-1"

    # 9. Save and retrieve report
    report = repo.save_report({
        "id": "rep-1",
        "research_run_id": "test-run-123",
        "content": {"summary": "Executive summary of CRM competitors", "comparison": {}},
    })
    assert report["id"] == "rep-1"

    retrieved_rep = repo.get_report("test-run-123")
    assert retrieved_rep is not None
    assert retrieved_rep["content"]["summary"] == "Executive summary of CRM competitors"
