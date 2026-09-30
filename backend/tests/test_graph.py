"""Integration tests for the LangGraph end-to-end research workflow (Task 12)."""

from unittest.mock import AsyncMock, patch
import pytest

from app.integrations.tavily import TavilyClient
from app.models.enums import JobStatus
from app.models.fact import Fact
from app.models.source import Source
from app.workflow.graph import create_research_graph, run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState


def test_research_graph_compilation():
    """Verify research graph compiles cleanly without configuration errors."""
    graph = create_research_graph()
    assert graph is not None


@pytest.mark.anyio
async def test_end_to_end_research_pipeline():
    """Verify a business question runs through Planner -> Parallel Research and populates state."""
    question = "Compare the major competitors in the Indian CRM market based on pricing and market presence."
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_search(query: str, research_run_id: str, max_results=None):
        entity = "Zoho" if "zoho" in query.lower() else "Freshworks" if "freshworks" in query.lower() else "Salesforce"
        return [
            Source(
                id=f"src-{entity.lower()}",
                research_run_id=research_run_id,
                url=f"https://{entity.lower()}.com/pricing",
                title=f"{entity} Official Pricing & History",
                domain=f"{entity.lower()}.com",
                evidence=f"{entity} was established in India and offers plans starting at ₹1,200/user/mo.",
            )
        ]

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=4)
        planner = Planner()

        final_state: ResearchState = await run_research_pipeline(
            question=question,
            research_id="run-e2e-crm-test",
            planner=planner,
            parallel_researcher=parallel_researcher,
        )

        # 1. Workflow Status
        assert final_state["workflow_status"] in ("checked", "researched")
        assert len(final_state["verification_results"]) >= 1
        assert final_state["research_id"] == "run-e2e-crm-test"
        assert final_state["question"] == question


        # 2. Planner Outputs
        assert len(final_state["assumptions"]) >= 1
        assert len(final_state["entities"]) >= 2
        assert len(final_state["research_jobs"]) >= 3

        # 3. Job Execution Outputs
        completed_jobs = [j for j in final_state["research_jobs"] if j.status == JobStatus.COMPLETED]
        assert len(completed_jobs) == len(final_state["research_jobs"])

        # 4. Extracted Facts & Provenance Invariants
        facts = final_state["facts"]
        assert len(facts) >= 3

        for fact in facts:
            assert isinstance(fact, Fact)
            assert fact.research_run_id == "run-e2e-crm-test"
            assert fact.entity != ""
            assert fact.attribute != ""
            assert fact.value != ""
            assert len(fact.source_ids) >= 1
            assert len(fact.evidence) >= 1
            assert fact.evidence[0].text != ""

        # 5. Collected Sources
        sources = final_state["sources"]
        assert len(sources) >= 1
        source_ids = {s.id for s in sources}
        # Every cited source ID in facts must exist in sources
        for fact in facts:
            for s_id in fact.source_ids:
                assert s_id in source_ids, f"Fact cited missing source ID {s_id}"
