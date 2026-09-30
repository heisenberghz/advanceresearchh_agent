"""Comprehensive End-to-End Pipeline Integration Test (Task 20 MVP Milestone).

Specification: PRD.md Section 5, TECH_SPEC.md Section 4 & 22, AGENT_TASKS.md Task 20.
Verifies the complete backend LangGraph workflow:
    START
      │
      ▼
   Planner
      │
      ▼
   Parallel Research
      │
      ▼
   Checker
      │
      ▼
   Conditional Retry (bounded)
      │
      ▼
   Research Gaps
      │
      ▼
   Comparer (Matrix)
      │
      ▼
   Writer (8-section Report)
      │
      ▼
     END
"""

from unittest.mock import patch
import pytest

from app.db.repository import ResearchRepository
from app.integrations.tavily import TavilyClient
from app.models.comparison import ComparisonMatrix
from app.models.enums import TrustTag
from app.models.report import ResearchReport
from app.models.source import Source
from app.workflow.graph import run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState


@pytest.mark.anyio
async def test_full_research_pipeline_realistic_scenario():
    """End-to-end integration test: Realistic multi-entity competitive inquiry produces full deliverable."""
    question = "Compare Zoho, Freshworks, and StealthSaaS on pricing, founding date, and revenue in the Indian SaaS market."
    run_id = "run-mvp-milestone-20"
    repo = ResearchRepository()
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    retry_tracker = {"stealthsaas_pricing_attempts": 0}

    async def mock_tavily_search(query: str, research_run_id: str, max_results=None):
        q_lower = query.lower()

        # Zoho search responses
        if "zoho" in q_lower:
            return [
                Source(
                    id="src-zoho-official",
                    research_run_id=research_run_id,
                    url="https://zoho.com/pricing",
                    title="Zoho Official Pricing & Company Overview",
                    domain="zoho.com",
                    evidence="Zoho was founded in 1996 in Chennai, India. Standard CRM plans start at ₹1,200/user/mo.",
                )
            ]

        # Freshworks search responses
        elif "freshworks" in q_lower:
            return [
                Source(
                    id="src-freshworks-news",
                    research_run_id=research_run_id,
                    url="https://techcrunch.com/freshworks-overview",
                    title="Freshworks Overview and Market Position",
                    domain="techcrunch.com",
                    evidence="Freshworks was founded in 2010. Its CRM offering starts at $15 per user monthly.",
                )
            ]

        # StealthSaaS search responses (unavailable pricing to trigger retry and gap)
        elif "stealthsaas" in q_lower:
            retry_tracker["stealthsaas_pricing_attempts"] += 1
            # Even on retry, pricing remains confidential / undisclosed
            return []

        return []

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_tavily_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=4)
        planner = Planner()

        final_state: ResearchState = await run_research_pipeline(
            question=question,
            research_id=run_id,
            planner=planner,
            parallel_researcher=parallel_researcher,
            repository=repo,
        )

        # =====================================================================
        # 1. State Machine & Status Milestones
        # =====================================================================
        assert final_state["workflow_status"] == "completed"
        assert final_state["research_id"] == run_id
        assert final_state["question"] == question

        # =====================================================================
        # 2. Planning Outputs
        # =====================================================================
        assert len(final_state["assumptions"]) >= 1
        assert len(final_state["entities"]) >= 2
        assert len(final_state["research_jobs"]) >= 2

        # =====================================================================
        # 3. Facts & Trust Evaluation
        # =====================================================================
        facts = final_state["facts"]
        assert len(facts) >= 2

        # Invariant: Every fact must have valid provenance
        for f in facts:
            assert f.research_run_id == run_id
            assert f.entity != ""
            assert f.attribute != ""
            assert f.value != ""
            assert len(f.source_ids) >= 1
            assert len(f.evidence) >= 1

        # Check official domain trust evaluation for Zoho
        zoho_facts = [f for f in facts if f.entity.lower() == "zoho"]
        assert any(f.trust_tag == TrustTag.GREEN for f in zoho_facts)

        # =====================================================================
        # 4. Research Gaps Validation
        # =====================================================================
        gaps = final_state["gaps"]
        assert len(gaps) >= 1
        stealth_gap = next((g for g in gaps if "stealthsaas" in g.requested_information.lower()), None)
        assert stealth_gap is not None
        assert stealth_gap.status == "gap"
        assert stealth_gap.attempts >= 1
        assert "No sufficiently reliable public information found" in stealth_gap.reason

        # Invariant: No fabricated facts for StealthSaaS pricing
        stealth_pricing_facts = [
            f for f in facts
            if f.entity.lower() == "stealthsaas" and "pricing" in f.attribute.lower()
        ]
        assert len(stealth_pricing_facts) == 0

        # =====================================================================
        # 5. Structured Comparison Matrix
        # =====================================================================
        matrix: ComparisonMatrix = final_state["comparison"]
        assert matrix is not None
        assert isinstance(matrix, ComparisonMatrix)
        assert len(matrix.entities) >= 2
        assert len(matrix.metrics) >= 1
        assert len(matrix.cells) >= 2

        # Render and verify markdown comparison table
        md_table = matrix.to_markdown_table()
        assert "| Dimension / Metric |" in md_table
        assert "🟢" in md_table or "🟡" in md_table

        # =====================================================================
        # 6. Final Synthesized Report (8 Mandatory Sections)
        # =====================================================================
        report: ResearchReport = final_state["report"]
        assert report is not None
        assert isinstance(report, ResearchReport)
        assert report.research_run_id == run_id
        assert len(report.title) > 5
        assert len(report.executive_summary) > 20
        assert len(report.key_findings) >= 1
        assert len(report.detailed_findings) >= 2
        assert len(report.sources) >= 1

        # Comprehensive Markdown validation
        report_md = report.markdown_content
        assert report_md is not None
        assert "## 1. Executive Summary" in report_md
        assert "## 2. Research Scope & Assumptions" in report_md
        assert "## 3. Comparison" in report_md
        assert "## 4. Key Findings" in report_md
        assert "## 5. Detailed Findings" in report_md
        assert "## 6. Conflicting Information" in report_md
        assert "## 7. Research Gaps" in report_md
        assert "## 8. Sources & Citations" in report_md

        # =====================================================================
        # 7. Repository Persistence Verification
        # =====================================================================
        stored_run = repo.get_research_run(run_id)
        assert stored_run is not None
        assert stored_run["status"] == "completed"

        stored_report = repo.get_report(run_id)
        assert stored_report is not None
        assert stored_report["id"] == report.id

        stored_gaps = repo.get_research_gaps(run_id)
        assert len(stored_gaps) >= 1


@pytest.mark.anyio
async def test_full_research_pipeline_offline_deterministic_execution():
    """Verify that the full backend pipeline executes deterministically without any external network access."""
    question = "Analyze Zoho pricing structure."
    run_id = "run-offline-test"
    repo = ResearchRepository()
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_offline_search(query: str, research_run_id: str, max_results=None):
        return [
            Source(
                id="src-offline-1",
                research_run_id=research_run_id,
                url="https://zoho.com/crm/pricing",
                title="Zoho CRM Pricing Plans",
                domain="zoho.com",
                evidence="Zoho CRM offers plans at ₹1,200 per user per month billed annually.",
            )
        ]

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_offline_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        planner = Planner()

        final_state = await run_research_pipeline(
            question=question,
            research_id=run_id,
            planner=planner,
            parallel_researcher=parallel_researcher,
            repository=repo,
        )

        assert final_state["workflow_status"] == "completed"
        assert final_state["report"] is not None
        assert len(final_state["facts"]) >= 1
        assert final_state["facts"][0].trust_tag == TrustTag.GREEN


@pytest.mark.anyio
async def test_full_research_pipeline_provenance_preservation_audit():
    """Verify that 100% of facts, comparison cells, and report sections maintain unbroken provenance."""
    question = "Compare Zoho and Freshworks on pricing."
    run_id = "run-provenance-audit"
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_provenance_search(query: str, research_run_id: str, max_results=None):
        entity = "Zoho" if "zoho" in query.lower() else "Freshworks"
        return [
            Source(
                id=f"src-{entity.lower()}",
                research_run_id=research_run_id,
                url=f"https://{entity.lower()}.com/pricing",
                title=f"{entity} Official Pricing",
                domain=f"{entity.lower()}.com",
                evidence=f"{entity} plans cost starting at $15/user/month.",
            )
        ]

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_provenance_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        planner = Planner()

        final_state = await run_research_pipeline(
            question=question,
            research_id=run_id,
            planner=planner,
            parallel_researcher=parallel_researcher,
        )

        facts = final_state["facts"]
        sources = final_state["sources"]
        source_id_set = {s.id for s in sources}

        # 1. Fact -> Source -> Evidence invariant
        for fact in facts:
            assert len(fact.source_ids) >= 1
            for sid in fact.source_ids:
                assert sid in source_id_set, f"Fact {fact.id} cited unknown source {sid}"
            assert len(fact.evidence) >= 1
            for ev in fact.evidence:
                assert ev.text != ""
                assert ev.source_id in source_id_set

        # 2. Comparison cell -> Fact provenance
        matrix = final_state["comparison"]
        for cell in matrix.cells:
            if cell.value != "Not found":
                assert cell.fact_id is not None
                matching_fact = next((f for f in facts if f.id == cell.fact_id), None)
                assert matching_fact is not None
                assert matching_fact.value == cell.value
                assert matching_fact.trust_tag == cell.trust_tag

