"""Automated test suite for Task 17 — Research Gaps & Missing Information.

Specification: PRD.md Section 5.3, TECH_SPEC.md Section 15, and AGENT_TASKS.md Task 17.
Key invariants:
- No fabricated values are created.
- Unverified, failing, or missing information is explicitly persisted as ResearchGap records.
- Gaps are included in workflow state and reach subsequent stages.
"""

from unittest.mock import patch
import pytest

from app.db.repository import ResearchRepository
from app.integrations.tavily import TavilyClient
from app.models.enums import JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact, VerificationResult
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.gaps import GapDetector
from app.workflow.graph import run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner, ResearchPlan
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState, create_initial_research_state


def test_no_gaps_when_all_topics_have_verified_facts():
    """Verify that when all jobs have at least one verified fact (GREEN/YELLOW), no gaps are created."""
    detector = GapDetector(repository=ResearchRepository())

    job = ResearchJob(
        id="job-1",
        research_run_id="run-1",
        description="Research Zoho Pricing",
        entity="Zoho",
        attribute="Pricing",
        status=JobStatus.COMPLETED,
        attempts=1,
    )
    fact = Fact(
        id="fact-1",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        verification_reason="Verified from official site.",
        source_ids=["src-1"],
        evidence=[Evidence(source_id="src-1", text="Plans start at ₹1,200/user/mo.")],
    )

    state: ResearchState = create_initial_research_state("run-1", "Zoho Pricing Question")
    state["research_jobs"] = [job]
    state["facts"] = [fact]

    gaps = detector.detect_gaps(state)
    assert len(gaps) == 0


def test_gap_detected_when_job_yields_zero_facts():
    """Verify that a job yielding no facts creates an explicit ResearchGap without fabricating a value."""
    detector = GapDetector(repository=ResearchRepository())

    job = ResearchJob(
        id="job-pricing",
        research_run_id="run-1",
        description="Research StealthCo Pricing",
        entity="StealthCo",
        attribute="Pricing",
        status=JobStatus.COMPLETED,
        attempts=2,
    )

    state: ResearchState = create_initial_research_state("run-1", "StealthCo Pricing")
    state["research_jobs"] = [job]
    state["facts"] = []
    state["retry_counts"] = {"job-pricing": 2}

    gaps = detector.detect_gaps(state)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.requested_information == "StealthCo Pricing"
    assert "No sufficiently reliable public information found" in gap.reason
    assert gap.attempts == 2
    assert gap.status == "gap"


def test_gap_detected_when_job_fails():
    """Verify that a failed research job creates an explicit ResearchGap noting the execution failure."""
    detector = GapDetector(repository=ResearchRepository())

    job = ResearchJob(
        id="job-fail",
        research_run_id="run-1",
        description="Research PrivateCo Market Share",
        entity="PrivateCo",
        attribute="Market Share",
        status=JobStatus.FAILED,
        attempts=2,
        error="Search timeout after multiple retries",
    )

    state: ResearchState = create_initial_research_state("run-1", "PrivateCo Market Share")
    state["research_jobs"] = [job]
    state["facts"] = []

    gaps = detector.detect_gaps(state)
    assert len(gaps) == 1
    assert gaps[0].requested_information == "PrivateCo Market Share"
    assert "Research execution failed" in gaps[0].reason
    assert "Search timeout" in gaps[0].reason
    assert gaps[0].attempts == 2


def test_gap_detected_when_all_extracted_facts_are_unverified_or_red():
    """Verify that if all facts for an entity/attribute are marked RED, a ResearchGap is created."""
    detector = GapDetector(repository=ResearchRepository())

    job = ResearchJob(
        id="job-revenue",
        research_run_id="run-1",
        description="Research RumorCorp FY25 Revenue",
        entity="RumorCorp",
        attribute="Revenue",
        status=JobStatus.COMPLETED,
        attempts=2,
    )
    # Extracted claim that failed verification
    red_fact = Fact(
        id="fact-unverified",
        research_run_id="run-1",
        entity="RumorCorp",
        attribute="Revenue",
        value="$500M",
        trust_tag=TrustTag.RED,
        verification_status=VerificationStatus.UNSUPPORTED,
        verification_reason="Ungrounded claim; citation absent from all retrieved sources.",
        source_ids=[],
        evidence=[],
    )

    state: ResearchState = create_initial_research_state("run-1", "RumorCorp Revenue")
    state["research_jobs"] = [job]
    state["facts"] = [red_fact]
    state["retry_counts"] = {"job-revenue": 2}

    gaps = detector.detect_gaps(state)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.requested_information == "RumorCorp Revenue"
    assert "Information could not be verified from reliable sources" in gap.reason
    assert gap.attempts == 2


def test_gap_persistence_in_repository():
    """Verify that GapDetector persists gaps into ResearchRepository and retrieves them cleanly."""
    from app.db.client import DatabaseClient
    repo = ResearchRepository(DatabaseClient(None))
    detector = GapDetector(repository=repo)

    gap = ResearchGap(
        id="gap-persist-1",
        research_run_id="run-persist",
        requested_information="Enterprise Discount Rates",
        reason="Information is strictly proprietary.",
        attempts=3,
    )

    persisted = detector.persist_gaps([gap])
    assert len(persisted) == 1
    assert persisted[0].id == "gap-persist-1"

    # Query from repository
    stored_gaps = repo.get_research_gaps("run-persist")
    assert len(stored_gaps) == 1
    assert stored_gaps[0]["id"] == "gap-persist-1"
    assert stored_gaps[0]["requested_information"] == "Enterprise Discount Rates"
    assert stored_gaps[0]["attempts"] == 3


@pytest.mark.anyio
async def test_langgraph_pipeline_persists_gaps_on_unverified_research():
    """End-to-end integration test: Pipeline produces facts for verified entities and gaps for missing ones."""
    run_id = "run-e2e-gaps"
    question = "Compare Zoho and StealthCo on pricing."
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_search(query: str, research_run_id: str, max_results=None):
        if "zoho" in query.lower():
            return [
                Source(
                    id="src-zoho",
                    research_run_id=research_run_id,
                    url="https://zoho.com/pricing",
                    title="Zoho Official Pricing",
                    domain="zoho.com",
                    evidence="Zoho offers standard plans starting at ₹1,200/user/mo.",
                )
            ]
        # StealthCo has no search results available
        return []

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        planner = Planner()

        # Mock planner to plan 2 distinct jobs
        mock_plan = ResearchPlan(
            research_run_id=run_id,
            question=question,
            assumptions=["Comparing Indian CRM competitors"],
            entities=["Zoho", "StealthCo"],
            comparison_dimensions=["Pricing"],
            research_jobs=[
                ResearchJob(
                    id="job-zoho-pricing",
                    research_run_id=run_id,
                    description="Research Zoho Pricing",
                    entity="Zoho",
                    attribute="Pricing",
                    status=JobStatus.PENDING,
                ),
                ResearchJob(
                    id="job-stealthco-pricing",
                    research_run_id=run_id,
                    description="Research StealthCo Pricing",
                    entity="StealthCo",
                    attribute="Pricing",
                    status=JobStatus.PENDING,
                ),
            ],
        )

        with patch.object(planner, "plan", return_value=mock_plan):
            from app.db.client import DatabaseClient
            repo = ResearchRepository(DatabaseClient(None))
            gap_detector = GapDetector(repository=repo)

            final_state = await run_research_pipeline(
                question=question,
                research_id=run_id,
                planner=planner,
                parallel_researcher=parallel_researcher,
                gap_detector=gap_detector,
                repository=repo,
            )

            # Invariant 1: Zoho pricing is verified (GREEN)
            zoho_facts = [f for f in final_state["facts"] if f.entity.lower() == "zoho"]
            assert len(zoho_facts) >= 1
            assert zoho_facts[0].trust_tag == TrustTag.GREEN

            # Invariant 2: StealthCo pricing was NOT fabricated as a fact
            stealth_facts = [f for f in final_state["facts"] if f.entity.lower() == "stealthco"]
            assert len(stealth_facts) == 0

            # Invariant 3: StealthCo pricing is explicitly registered as a ResearchGap
            gaps = final_state["gaps"]
            assert len(gaps) >= 1
            stealth_gap = next((g for g in gaps if "stealthco" in g.requested_information.lower()), None)
            assert stealth_gap is not None
            assert stealth_gap.status == "gap"
            assert "No sufficiently reliable public information found" in stealth_gap.reason

            # Invariant 4: Gap was persisted to repository
            stored_gaps = repo.get_research_gaps(run_id)
            assert len(stored_gaps) >= 1
            assert any("stealthco" in g["requested_information"].lower() for g in stored_gaps)
