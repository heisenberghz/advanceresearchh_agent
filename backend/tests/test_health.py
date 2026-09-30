"""Tests for backend health, root endpoints, and configuration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify root endpoint responds with basic service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ResearchOps API"
    assert data["status"] == "operational"
    assert "health" in data


def test_health_endpoint(client):
    """Verify health endpoint responds with healthy status and safe config summary."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ResearchOps Backend"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "configuration" in data

    config = data["configuration"]
    assert "is_research_ready" in config
    assert "missing_keys" in config
    assert "research_model" in config
    assert "writer_model" in config
    assert config["max_research_retries"] in (1, 2)
    assert config["max_searches_per_job"] in (2, 3)

    # CRITICAL: Verify no secrets or sensitive raw keys leaked in payload
    payload_str = str(data).lower()
    assert "secret" not in payload_str
    assert "api_key" not in payload_str or "missing_keys" in payload_str


def test_config_missing_keys_detection():
    """Verify configuration correctly flags missing required external keys."""
    # Settings without any env overrides
    settings = Settings(
        OPENROUTER_API_KEY=None,
        TAVILY_API_KEY=None,
        SUPABASE_URL=None,
        SUPABASE_KEY=None,
    )
    missing = settings.check_missing_required_keys()
    assert "OPENROUTER_API_KEY" in missing
    assert "TAVILY_API_KEY" in missing
    assert "SUPABASE_URL" in missing
    assert "SUPABASE_KEY" in missing

    with pytest.raises(ValueError) as exc_info:
        settings.ensure_research_configured()
    assert "Missing required configuration for research execution" in str(exc_info.value)


def test_config_complete_keys_validation():
    """Verify configuration recognizes when all keys are populated."""
    settings = Settings(
        OPENROUTER_API_KEY="sk-test-key",
        TAVILY_API_KEY="tvly-test-key",
        SUPABASE_URL="https://mock.supabase.co",
        SUPABASE_KEY="mock-supabase-key",
    )
    missing = settings.check_missing_required_keys()
    assert len(missing) == 0
    # ensure_research_configured should not raise
    settings.ensure_research_configured()
