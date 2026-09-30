"""Automated test suite for Task 19 — Writer & Final Report Generation.

Specification: PRD.md Section 5.5, TECH_SPEC.md Section 21 & 22, and AGENT_TASKS.md Task 19.
Key invariants:
- Contains all 8 mandatory sections (Executive Summary, Assumptions, Comparison, Key Findings,
  Detailed Findings, Conflicting Information, Research Gaps, Sources).
- Uses only verified research state (no hallucinated claims).
- Explicitly documents conflicts and research gaps.
- Preserves full provenance and citations.
- Persists report to repository.
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.db.repository import ResearchRepository
from app.integrations.openrouter import OpenRouterClient
from app.integrations.tavily import TavilyClient
from app.models.comparison import ComparisonCell, ComparisonMatrix
from app.models.conflict import CompetingValue, Conflict
from app.models.enums import ConflictStatus, JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.models.report import ResearchReport
from app.models.source import Evidence, Source
from app.workflow.graph import run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner, ResearchPlan
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState, create_initial_research_state
from app.workflow.writer import StructuredExecutiveSynthesis, Writer


def test_writer_generates_all_mandatory_sections_in_report():
    """Verify that Writer produces a report containing all 8 required sections."""
    repo = ResearchRepository()
    writer = Writer(repository=repo)

    fact = Fact(
        id="f-1",
        research_run_id="run-writer-1",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        source_ids=["src-1"],
        evidence=[Evidence(source_id="src-1", text="Starting at ₹1,200/user/mo.")],
    )
    source = Source(
        id="src-1",
        research_run_id="run-writer-1",
        url="https://zoho.com/pricing",
        title="Zoho Pricing",
        domain="zoho.com",
    )
    gap = ResearchGap(
        id="gap-1",
        research_run_id="run-writer-1",
        requested_information="StealthCo Pricing",
        reason="Information undisclosed.",
        attempts=2,
    )
    conflict = Conflict(
        id="conf-1",
        research_run_id="run-writer-1",
        entity="LeadSquared",
        attribute="Revenue",
        description="Conflicting revenue disclosures",
        competing_values=[
            CompetingValue(value="₹100 Cr", source_url="https://a.com", evidence="₹100 Cr"),
            CompetingValue(value="₹130 Cr", source_url="https://b.com", evidence="₹130 Cr"),
        ],
        supporting_sources=["src-1"],
    )

    state: ResearchState = create_initial_research_state("run-writer-1", "Compare CRM options")
    state["assumptions"] = ["Focus on Indian enterprise CRM market."]
    state["entities"] = ["Zoho", "StealthCo", "LeadSquared"]
    state["facts"] = [fact]
    state["sources"] = [source]
    state["gaps"] = [gap]
    state["conflicts"] = [conflict]

    import asyncio
    report: ResearchReport = asyncio.run(writer.generate_report(state))

    # Mandatory Structural Checks
    assert report.research_run_id == "run-writer-1"
    assert len(report.title) > 5
    assert len(report.executive_summary) > 20
    assert len(report.assumptions) == 1
    assert report.comparison is not None
    assert len(report.key_findings) >= 1
    assert len(report.detailed_findings) == 1
    assert len(report.conflicting_information) == 1
    assert len(report.research_gaps) == 1
    assert len(report.sources) == 1

    # Rendered Markdown Checks (all 8 sections)
    md = report.to_markdown()
    assert "## 1. Executive Summary" in md
    assert "## 2. Research Scope & Assumptions" in md
    assert "## 3. Comparison" in md
    assert "## 4. Key Findings" in md
    assert "## 5. Detailed Findings" in md
    assert "## 6. Conflicting Information" in md
    assert "## 7. Research Gaps" in md
    assert "## 8. Sources & Citations" in md


def test_writer_preserves_conflicts_and_gaps_in_narrative():
    """Verify narrative synthesis explicitly acknowledges conflicts and research gaps."""
    writer = Writer(repository=ResearchRepository())

    fact = Fact(
        id="f-z",
        research_run_id="run-cg",
        entity="Zoho",
        attribute="Founded",
        value="1996",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        source_ids=["s-1"],
        evidence=[Evidence(source_id="s-1", text="Founded 1996")],
    )
    gap = ResearchGap(
        id="gap-s",
        research_run_id="run-cg",
        requested_information="SecretCo Valuation",
        reason="No audited financials available.",
        attempts=2,
    )
    conflict = Conflict(
        id="conf-lead",
        research_run_id="run-cg",
        entity="LeadSquared",
        attribute="Revenue",
        description="Conflicting revenue disclosures",
        competing_values=[
            CompetingValue(value="₹100 Cr", source_url="https://a.com", evidence="100"),
            CompetingValue(value="₹130 Cr", source_url="https://b.com", evidence="130"),
        ],
        supporting_sources=["s-1"],
    )

    state: ResearchState = create_initial_research_state("run-cg", "Evaluate Indian SaaS")
    state["entities"] = ["Zoho", "SecretCo", "LeadSquared"]
    state["facts"] = [fact]
    state["gaps"] = [gap]
    state["conflicts"] = [conflict]

    import asyncio
    report = asyncio.run(writer.generate_report(state))

    assert "research gap" in report.executive_summary.lower()
    assert "conflict" in report.executive_summary.lower()
    findings_str = " ".join(report.key_findings).lower()
    assert "secretco" in findings_str or "research gaps" in findings_str


def test_writer_persists_report_to_repository():
    """Verify that generated reports are stored and retrievable via ResearchRepository."""
    repo = ResearchRepository()
    writer = Writer(repository=repo)

    state: ResearchState = create_initial_research_state("run-persisted-rep", "What is Freshworks pricing?")
    state["entities"] = ["Freshworks"]

    import asyncio
    report = asyncio.run(writer.generate_report(state))

    stored = repo.get_report("run-persisted-rep")
    assert stored is not None
    assert stored["id"] == report.id
    assert stored["research_run_id"] == "run-persisted-rep"


@pytest.mark.anyio
async def test_writer_llm_synthesis_with_mock_openrouter():
    """Verify that when OpenRouter is configured, Writer uses LLM structured output."""
    mock_openrouter = OpenRouterClient(api_key="sk-or-mock-test")

    mock_synthesis = StructuredExecutiveSynthesis(
        title="Comprehensive Indian CRM Competitive Analysis 2026",
        executive_summary="This strategic report provides verified comparative insights across top CRM platforms.",
        key_findings=[
            "Zoho offers the most competitive entry pricing at ₹1,200/user/mo.",
            "Enterprise contract terms remain a research gap for private vendors.",
        ],
    )

    with patch.object(mock_openrouter, "chat_structured", new=AsyncMock(return_value=mock_synthesis)):
        writer = Writer(openrouter_client=mock_openrouter, repository=ResearchRepository())

        state: ResearchState = create_initial_research_state("run-llm-rep", "Analyze CRM market")
        state["entities"] = ["Zoho"]

        report = await writer.generate_report(state)
        assert report.title == "Comprehensive Indian CRM Competitive Analysis 2026"
        assert "strategic report" in report.executive_summary
        assert len(report.key_findings) == 2


@pytest.mark.anyio
async def test_langgraph_pipeline_produces_final_report():
    """End-to-end integration test: Pipeline executes from question to final report."""
    question = "Compare Zoho and Salesforce on market entry and pricing."
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_search(query: str, research_run_id: str, max_results=None):
        entity = "Zoho" if "zoho" in query.lower() else "Salesforce"
        return [
            Source(
                id=f"src-{entity.lower()}",
                research_run_id=research_run_id,
                url=f"https://{entity.lower()}.com",
                title=f"{entity} Official",
                domain=f"{entity.lower()}.com",
                evidence=f"{entity} provides CRM software starting at ₹1,200/mo.",
            )
        ]

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        planner = Planner()

        mock_plan = ResearchPlan(
            research_run_id="run-final-e2e",
            question=question,
            assumptions=["Indian enterprise context"],
            entities=["Zoho", "Salesforce"],
            comparison_dimensions=["Pricing"],
            research_jobs=[
                ResearchJob(
                    id="job-z",
                    research_run_id="run-final-e2e",
                    description="Zoho Pricing",
                    entity="Zoho",
                    attribute="Pricing",
                ),
                ResearchJob(
                    id="job-s",
                    research_run_id="run-final-e2e",
                    description="Salesforce Pricing",
                    entity="Salesforce",
                    attribute="Pricing",
                ),
            ],
        )

        with patch.object(planner, "plan", return_value=mock_plan):
            repo = ResearchRepository()
            final_state = await run_research_pipeline(
                question=question,
                research_id="run-final-e2e",
                planner=planner,
                parallel_researcher=parallel_researcher,
            )

            # 1. State completed
            assert final_state["workflow_status"] == "completed"

            # 2. Report present and populated
            report: ResearchReport = final_state["report"]
            assert report is not None
            assert isinstance(report, ResearchReport)
            assert report.research_run_id == "run-final-e2e"
            assert len(report.executive_summary) > 20
            assert report.comparison is not None
            assert len(report.detailed_findings) >= 2

            # 3. Report markdown is comprehensive
            md = report.markdown_content
            assert md is not None
            assert "## 1. Executive Summary" in md
            assert "## 3. Comparison" in md
            assert "## 8. Sources & Citations" in md
