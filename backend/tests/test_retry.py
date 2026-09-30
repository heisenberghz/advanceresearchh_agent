"""Unit tests for Research Retry Loop (Task 16)."""

from unittest.mock import patch
import pytest

from app.integrations.tavily import TavilyClient
from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.checker import Checker
from app.workflow.graph import create_research_graph
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner
from app.workflow.researcher import Researcher
from app.workflow.retry import RetryCoordinator, get_retry_coordinator
from app.workflow.state import ResearchState, create_initial_research_state


def test_retry_identifies_only_unsupported_or_failing_jobs():
    """RetryCoordinator must selectively target only failing jobs, not successful ones."""
    coordinator = get_retry_coordinator(max_retries=2)

    job_good = ResearchJob(
        id="job-good",
        research_run_id="run-1",
        description="Research Zoho Pricing",
        entity="Zoho",
        status=JobStatus.COMPLETED,
    )
    job_bad = ResearchJob(
        id="job-bad",
        research_run_id="run-1",
        description="Research ObscureCRM Pricing",
        entity="ObscureCRM",
        status=JobStatus.COMPLETED,
    )

    facts = [
        Fact(
            id="f-good",
            research_run_id="run-1",
            entity="Zoho",
            attribute="Pricing",
            value="₹1,200/user/mo",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["s-zoho"],
        ),
        Fact(
            id="f-bad",
            research_run_id="run-1",
            entity="ObscureCRM",
            attribute="Pricing",
            value="Unknown",
            trust_tag=TrustTag.RED,
            verification_status=VerificationStatus.UNSUPPORTED,
            source_ids=[],
        ),
    ]

    state: ResearchState = {
        "research_id": "run-1",
        "question": "Compare CRMs",
        "assumptions": [],
        "entities": ["Zoho", "ObscureCRM"],
        "research_jobs": [job_good, job_bad],
        "research_results": [],
        "facts": facts,
        "sources": [],
        "verification_results": [],
        "conflicts": [],
        "gaps": [],
        "comparison": None,
        "report": None,
        "retry_counts": {},
        "workflow_status": "checked",
        "errors": [],
    }

    candidates = coordinator.identify_retry_candidates(state)

    # Only job_bad should be selected
    assert len(candidates) == 1
    assert candidates[0].id == "job-bad"
    assert coordinator.should_retry(state) is True


def test_retry_respects_hard_retry_limit_to_prevent_infinite_loops():
    """Once a job reaches max_retries, it must no longer qualify for retry."""
    coordinator = get_retry_coordinator(max_retries=2)

    job_failed = ResearchJob(
        id="job-failed",
        research_run_id="run-1",
        description="Research Missing Info",
        entity="PhantomCompany",
        status=JobStatus.FAILED,
    )

    state: ResearchState = {
        "research_id": "run-1",
        "question": "Question",
        "assumptions": [],
        "entities": ["PhantomCompany"],
        "research_jobs": [job_failed],
        "research_results": [],
        "facts": [],
        "sources": [],
        "verification_results": [],
        "conflicts": [],
        "gaps": [],
        "comparison": None,
        "report": None,
        "retry_counts": {"job-failed": 2},  # Reached max_retries (2)
        "workflow_status": "checked",
        "errors": [],
    }

    candidates = coordinator.identify_retry_candidates(state)
    assert len(candidates) == 0
    assert coordinator.should_retry(state) is False


def test_retry_prepares_targeted_query_modifiers():
    """Prepared retry jobs must increment attempts and enrich search queries."""
    coordinator = get_retry_coordinator(max_retries=2)

    job = ResearchJob(
        id="job-1",
        research_run_id="run-1",
        description="Search LeadSquared enterprise pricing",
        entity="LeadSquared",
    )

    prepared = coordinator.prepare_retry_job(job, attempt=0)

    assert prepared.attempts == 1
    assert prepared.status == JobStatus.RUNNING
    assert "official pricing overview" in prepared.description
    assert "Search LeadSquared enterprise pricing" in prepared.description


@pytest.mark.anyio
async def test_langgraph_executes_retry_loop_until_completion():
    """LangGraph research graph must conditionally loop to retry weak research and terminate cleanly."""
    mock_tavily = TavilyClient(api_key="tvly-mock-key")
    call_counts = {"LeadSquared": 0}

    async def mock_search_with_retry(query: str, research_run_id: str, max_results=None):
        if "zoho" in query.lower():
            return [
                Source(
                    id="src-zoho",
                    research_run_id=research_run_id,
                    url="https://zoho.com/pricing",
                    title="Zoho Official Pricing",
                    domain="zoho.com",
                    evidence="Zoho Standard plan starts at ₹1,200/user/mo.",
                )
            ]
        elif "leadsquared" in query.lower():
            call_counts["LeadSquared"] += 1
            if call_counts["LeadSquared"] == 1:
                # First attempt: fails to locate information
                return []
            else:
                # Retry attempt: finds grounded pricing!
                return [
                    Source(
                        id="src-lead-2",
                        research_run_id=research_run_id,
                        url="https://leadsquared.com/pricing",
                        title="LeadSquared Official Pricing",
                        domain="leadsquared.com",
                        evidence="LeadSquared Lite plan starts at ₹1,500/user/mo.",
                    )
                ]
        return []


    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_search_with_retry):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        coordinator = RetryCoordinator(parallel_researcher=parallel_researcher, max_retries=2)
        checker = Checker()

        # Build initial state with 2 jobs
        job_zoho = ResearchJob(
            id="job-zoho",
            research_run_id="run-retry-e2e",
            description="Find Zoho pricing",
            entity="Zoho",
        )
        job_lead = ResearchJob(
            id="job-lead",
            research_run_id="run-retry-e2e",
            description="Find LeadSquared pricing",
            entity="LeadSquared",
        )

        mock_planner = Planner()
        async def mock_plan_1(question: str, research_run_id: str):
            from app.workflow.planner import ResearchPlan
            return ResearchPlan(
                question=question,
                assumptions=["Testing"],
                entities=["Zoho", "LeadSquared"],
                comparison_dimensions=["Pricing"],
                research_jobs=[job_zoho, job_lead],
            )
        mock_planner.plan = mock_plan_1

        initial_state = create_initial_research_state("run-retry-e2e", "Compare Zoho and LeadSquared")
        initial_state["entities"] = ["Zoho", "LeadSquared"]
        initial_state["research_jobs"] = [job_zoho, job_lead]

        graph = create_research_graph(
            planner=mock_planner,
            parallel_researcher=parallel_researcher,
            checker=checker,
            retry_coordinator=coordinator,
        )

        final_state: ResearchState = await graph.ainvoke(initial_state)

        # 1. Loop terminated successfully
        assert final_state["workflow_status"] in ("checked", "compared", "completed")

        # 2. Retry was triggered for LeadSquared
        assert call_counts["LeadSquared"] >= 2
        assert final_state["retry_counts"].get("job-lead", 0) >= 1

        # 3. Facts from both entities are present and verified
        entities_with_facts = {f.entity for f in final_state["facts"]}
        assert "Zoho" in entities_with_facts
        assert "LeadSquared" in entities_with_facts

        # 4. Verified facts exist
        verified_facts = [f for f in final_state["facts"] if f.trust_tag == TrustTag.GREEN]
        assert len(verified_facts) >= 1


@pytest.mark.anyio
async def test_retry_loop_terminates_safely_when_information_permanently_unavailable():
    """When a job permanently produces no evidence, the retry loop must terminate at max_retries without looping infinitely."""
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_empty_search(query: str, research_run_id: str, max_results=None):
        return []  # Permanently empty

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_empty_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        coordinator = RetryCoordinator(parallel_researcher=parallel_researcher, max_retries=2)
        checker = Checker()

        job_empty = ResearchJob(
            id="job-nonexistent",
            research_run_id="run-term-test",
            description="Find SecretPlan pricing",
            entity="NonExistentCorp",
        )

        mock_planner = Planner()
        async def mock_plan_2(question: str, research_run_id: str):
            from app.workflow.planner import ResearchPlan
            return ResearchPlan(
                question=question,
                assumptions=["Testing"],
                entities=["NonExistentCorp"],
                comparison_dimensions=["Pricing"],
                research_jobs=[job_empty],
            )
        mock_planner.plan = mock_plan_2


        initial_state = create_initial_research_state("run-term-test", "Secret info")
        initial_state["research_jobs"] = [job_empty]

        graph = create_research_graph(
            planner=mock_planner,
            parallel_researcher=parallel_researcher,
            checker=checker,
            retry_coordinator=coordinator,
        )

        final_state: ResearchState = await graph.ainvoke(initial_state)

        # Must exit to terminal workflow state
        assert final_state["workflow_status"] in ("checked", "compared", "completed")
        # Reached exact max_retries limit
        assert final_state["retry_counts"].get("job-nonexistent", 0) == 2

