"""Unit tests for the Planner workflow component."""

from unittest.mock import AsyncMock, patch
import pytest

from app.integrations.openrouter import OpenRouterClient
from app.models.enums import JobStatus
from app.models.job import ResearchJob
from app.workflow.planner import Planner, RawPlannerJob, RawPlannerOutput, ResearchPlan


@pytest.mark.anyio
async def test_planner_rejects_empty_question():
    """Verify Planner raises ValueError for questions that are too short."""
    planner = Planner(OpenRouterClient(api_key=None))
    with pytest.raises(ValueError) as exc_info:
        await planner.plan(question="who?", research_run_id="run-1")
    assert "at least 5 characters" in str(exc_info.value)


@pytest.mark.anyio
async def test_planner_heuristic_decomposition():
    """Verify Planner heuristic generator produces structured jobs for CRM questions."""
    planner = Planner(OpenRouterClient(api_key=None))
    plan: ResearchPlan = await planner.plan(
        question="Compare major competitors in the Indian CRM market",
        research_run_id="run-test-12345",
    )

    assert isinstance(plan, ResearchPlan)
    assert plan.question == "Compare major competitors in the Indian CRM market"
    assert len(plan.assumptions) >= 1
    assert "Zoho" in plan.entities
    assert len(plan.comparison_dimensions) >= 3
    assert len(plan.research_jobs) >= 4

    # Verify each job is a valid ResearchJob with unique IDs
    job_ids = set()
    for job in plan.research_jobs:
        assert isinstance(job, ResearchJob)
        assert job.research_run_id == "run-test-12345"
        assert job.status == JobStatus.PENDING
        assert job.id.startswith("job-run-test-")
        assert job.id not in job_ids
        job_ids.add(job.id)


@pytest.mark.anyio
async def test_planner_llm_structured_decomposition():
    """Verify Planner integrates with OpenRouter structured output."""
    mock_client = OpenRouterClient(api_key="sk-mock-key")

    mock_raw_output = RawPlannerOutput(
        assumptions=["Focus on Indian market", "Enterprise segment"],
        entities=["Zoho", "Salesforce", "LeadSquared"],
        comparison_dimensions=["Pricing", "Deployment", "Founding Year"],
        jobs=[
            RawPlannerJob(
                description="Investigate Zoho CRM enterprise tier pricing and founding year",
                entity="Zoho",
                attribute="Pricing & Founded",
            ),
            RawPlannerJob(
                description="Investigate Salesforce Indian cloud pricing and entry tiers",
                entity="Salesforce",
                attribute="Pricing",
            ),
            RawPlannerJob(
                description="Investigate LeadSquared market positioning and founding year",
                entity="LeadSquared",
                attribute="Overview",
            ),
        ],
    )

    with patch.object(mock_client, "chat_structured", new_callable=AsyncMock) as mock_structured:
        mock_structured.return_value = mock_raw_output

        planner = Planner(mock_client)
        plan: ResearchPlan = await planner.plan(
            question="Compare enterprise CRM solutions in India",
            research_run_id="run-77778888",
        )

        assert mock_structured.called
        assert plan.entities == ["Zoho", "Salesforce", "LeadSquared"]
        assert len(plan.research_jobs) == 3

        first_job = plan.research_jobs[0]
        assert first_job.entity == "Zoho"
        assert first_job.attribute == "Pricing & Founded"
        assert first_job.research_run_id == "run-77778888"
        assert first_job.status == JobStatus.PENDING
