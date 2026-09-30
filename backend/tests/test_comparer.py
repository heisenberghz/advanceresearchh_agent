"""Automated test suite for Task 18 — Comparer & Structured Comparison Matrices.

Specification: PRD.md Section 5.4, TECH_SPEC.md Section 20, and AGENT_TASKS.md Task 18.
Key invariants:
- Group facts by entity and metric.
- Preserve fact IDs, source citations, and trust tags.
- Represent missing values clearly as 'Not found' (never invent values).
- Link missing cells to explicit ResearchGap records when available.
- Annotate cells with conflict details if contradictions exist.
- Output clean Markdown comparison tables.
"""

from unittest.mock import patch
import pytest

from app.integrations.tavily import TavilyClient
from app.models.comparison import ComparisonCell, ComparisonMatrix
from app.models.conflict import CompetingValue, Conflict
from app.models.enums import ConflictStatus, JobStatus, TrustTag, VerificationStatus
from app.models.fact import Fact
from app.models.gap import ResearchGap
from app.models.job import ResearchJob
from app.models.source import Evidence, Source
from app.workflow.comparer import Comparer
from app.workflow.graph import run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner, ResearchPlan
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState, create_initial_research_state


def test_comparer_groups_facts_by_entity_and_metric():
    """Verify Comparer aligns facts into a complete 2D entity x metric grid."""
    comparer = Comparer()

    facts = [
        Fact(
            id="f-zoho-hq",
            research_run_id="run-1",
            entity="Zoho",
            attribute="Headquarters",
            value="Chennai, India",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["s-1"],
            evidence=[Evidence(source_id="s-1", text="Zoho is headquartered in Chennai.")],
        ),
        Fact(
            id="f-zoho-founded",
            research_run_id="run-1",
            entity="Zoho",
            attribute="Founded",
            value="1996",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["s-1"],
            evidence=[Evidence(source_id="s-1", text="Founded in 1996.")],
        ),
        Fact(
            id="f-fresh-hq",
            research_run_id="run-1",
            entity="Freshworks",
            attribute="Headquarters",
            value="San Mateo, CA",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["s-2"],
            evidence=[Evidence(source_id="s-2", text="Freshworks is based in San Mateo.")],
        ),
        Fact(
            id="f-fresh-founded",
            research_run_id="run-1",
            entity="Freshworks",
            attribute="Founded",
            value="2010",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["s-2"],
            evidence=[Evidence(source_id="s-2", text="Freshworks was founded in 2010.")],
        ),
    ]

    matrix = comparer.build_matrix(
        facts=facts,
        entities=["Zoho", "Freshworks"],
        metrics=["Headquarters", "Founded"],
    )

    assert matrix.entities == ["Zoho", "Freshworks"]
    assert matrix.metrics == ["Headquarters", "Founded"]
    assert len(matrix.cells) == 4

    cell_zoho_hq = matrix.get_cell("Zoho", "Headquarters")
    assert cell_zoho_hq is not None
    assert cell_zoho_hq.value == "Chennai, India"
    assert cell_zoho_hq.trust_tag == TrustTag.GREEN
    assert cell_zoho_hq.fact_id == "f-zoho-hq"
    assert "s-1" in cell_zoho_hq.source_ids

    cell_fresh_founded = matrix.get_cell("Freshworks", "Founded")
    assert cell_fresh_founded is not None
    assert cell_fresh_founded.value == "2010"
    assert cell_fresh_founded.trust_tag == TrustTag.GREEN


def test_comparer_prioritizes_verified_green_over_red_facts():
    """Verify that when multiple facts exist for a metric, the verified GREEN fact is preferred."""
    comparer = Comparer()

    green_fact = Fact(
        id="f-green",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Pricing",
        value="₹1,200/user/mo",
        trust_tag=TrustTag.GREEN,
        verification_status=VerificationStatus.VERIFIED,
        source_ids=["src-official"],
        evidence=[Evidence(source_id="src-official", text="₹1,200 per user per month")],
    )
    red_fact = Fact(
        id="f-red",
        research_run_id="run-1",
        entity="Zoho",
        attribute="Pricing",
        value="$50/user/mo",
        trust_tag=TrustTag.RED,
        verification_status=VerificationStatus.UNSUPPORTED,
        source_ids=[],
        evidence=[],
    )

    matrix = comparer.build_matrix(
        facts=[red_fact, green_fact],
        entities=["Zoho"],
        metrics=["Pricing"],
    )

    cell = matrix.get_cell("Zoho", "Pricing")
    assert cell is not None
    assert cell.value == "₹1,200/user/mo"
    assert cell.trust_tag == TrustTag.GREEN
    assert cell.fact_id == "f-green"


def test_comparer_represents_missing_values_as_not_found():
    """Verify that missing entity attributes are explicitly marked 'Not found' with RED tag (no invented values)."""
    comparer = Comparer()

    facts = [
        Fact(
            id="f-zoho-pricing",
            research_run_id="run-1",
            entity="Zoho",
            attribute="Pricing",
            value="₹1,200/user/mo",
            trust_tag=TrustTag.GREEN,
            verification_status=VerificationStatus.VERIFIED,
            source_ids=["src-1"],
            evidence=[Evidence(source_id="src-1", text="Plans start at ₹1,200.")],
        )
    ]

    matrix = comparer.build_matrix(
        facts=facts,
        entities=["Zoho", "StealthCo"],
        metrics=["Pricing"],
    )

    cell_stealth = matrix.get_cell("StealthCo", "Pricing")
    assert cell_stealth is not None
    assert cell_stealth.value == "Not found"
    assert cell_stealth.trust_tag == TrustTag.RED
    assert cell_stealth.fact_id is None
    assert cell_stealth.source_ids == []


def test_comparer_links_cells_to_research_gaps():
    """Verify that missing cells link to corresponding ResearchGap records when available."""
    comparer = Comparer()

    gap = ResearchGap(
        id="gap-stealth-pricing",
        research_run_id="run-1",
        requested_information="StealthCo Pricing",
        reason="No public pricing disclosures identified.",
        attempts=2,
    )

    matrix = comparer.build_matrix(
        facts=[],
        entities=["StealthCo"],
        metrics=["Pricing"],
        gaps=[gap],
    )

    cell = matrix.get_cell("StealthCo", "Pricing")
    assert cell is not None
    assert cell.value == "Not found"
    assert cell.gap_id == "gap-stealth-pricing"
    assert "No public pricing disclosures identified" in (cell.notes or "")


def test_comparer_includes_conflict_notes():
    """Verify that detected conflicts are noted in the comparison cell."""
    comparer = Comparer()

    fact = Fact(
        id="f-rev-1",
        research_run_id="run-1",
        entity="LeadSquared",
        attribute="Revenue",
        value="₹100 Cr",
        trust_tag=TrustTag.YELLOW,
        verification_status=VerificationStatus.VERIFIED,
        source_ids=["src-a"],
        evidence=[Evidence(source_id="src-a", text="Reported ₹100 Cr.")],
    )
    conflict = Conflict(
        id="conf-1",
        research_run_id="run-1",
        entity="LeadSquared",
        attribute="Revenue",
        description="Divergent FY25 revenue filings: ₹100 Cr vs ₹130 Cr",
        competing_values=[
            CompetingValue(value="₹100 Cr", source_url="https://a.com", evidence="Reported ₹100 Cr."),
            CompetingValue(value="₹130 Cr", source_url="https://b.com", evidence="Reported ₹130 Cr."),
        ],
        supporting_sources=["src-a", "src-b"],
        status=ConflictStatus.UNRESOLVED,
    )

    matrix = comparer.build_matrix(
        facts=[fact],
        entities=["LeadSquared"],
        metrics=["Revenue"],
        conflicts=[conflict],
    )

    cell = matrix.get_cell("LeadSquared", "Revenue")
    assert cell is not None
    assert cell.value == "₹100 Cr"
    assert cell.notes is not None
    assert "Conflict detected" in cell.notes
    assert "₹100 Cr vs ₹130 Cr" in cell.notes


def test_comparison_matrix_to_markdown_table_formatting():
    """Verify that ComparisonMatrix renders a clean GitHub Markdown table with trust badges."""
    cells = [
        ComparisonCell(
            entity="Zoho",
            metric="Pricing",
            value="₹1,200/user/mo",
            trust_tag=TrustTag.GREEN,
        ),
        ComparisonCell(
            entity="Freshworks",
            metric="Pricing",
            value="$15/user/mo",
            trust_tag=TrustTag.GREEN,
        ),
        ComparisonCell(
            entity="Zoho",
            metric="Headquarters",
            value="Chennai, India",
            trust_tag=TrustTag.GREEN,
        ),
        ComparisonCell(
            entity="Freshworks",
            metric="Headquarters",
            value="San Mateo, CA",
            trust_tag=TrustTag.YELLOW,
        ),
    ]

    matrix = ComparisonMatrix(
        entities=["Zoho", "Freshworks"],
        metrics=["Pricing", "Headquarters"],
        cells=cells,
    )

    md = matrix.to_markdown_table()
    assert "| Dimension / Metric | Zoho | Freshworks |" in md
    assert "| Pricing | 🟢 ₹1,200/user/mo | 🟢 $15/user/mo |" in md
    assert "| Headquarters | 🟢 Chennai, India | 🟡 San Mateo, CA |" in md


@pytest.mark.anyio
async def test_langgraph_pipeline_produces_comparison_matrix():
    """End-to-end integration test: Full pipeline generates and populates state['comparison']."""
    question = "Compare Zoho and Freshworks on pricing."
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_search(query: str, research_run_id: str, max_results=None):
        entity = "Zoho" if "zoho" in query.lower() else "Freshworks"
        return [
            Source(
                id=f"src-{entity.lower()}",
                research_run_id=research_run_id,
                url=f"https://{entity.lower()}.com/pricing",
                title=f"{entity} Pricing",
                domain=f"{entity.lower()}.com",
                evidence=f"{entity} standard plan costs $15 per user monthly.",
            )
        ]

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_search):
        researcher = Researcher(tavily_client=mock_tavily)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=2)
        planner = Planner()

        mock_plan = ResearchPlan(
            research_run_id="run-compare-test",
            question=question,
            assumptions=["Comparing pricing"],
            entities=["Zoho", "Freshworks"],
            comparison_dimensions=["Pricing"],
            research_jobs=[
                ResearchJob(
                    id="job-zoho",
                    research_run_id="run-compare-test",
                    description="Research Zoho Pricing",
                    entity="Zoho",
                    attribute="Pricing",
                    status=JobStatus.PENDING,
                ),
                ResearchJob(
                    id="job-fresh",
                    research_run_id="run-compare-test",
                    description="Research Freshworks Pricing",
                    entity="Freshworks",
                    attribute="Pricing",
                    status=JobStatus.PENDING,
                ),
            ],
        )

        with patch.object(planner, "plan", return_value=mock_plan):
            final_state = await run_research_pipeline(
                question=question,
                research_id="run-compare-test",
                planner=planner,
                parallel_researcher=parallel_researcher,
            )

            # Invariant: final_state['comparison'] is populated with a valid ComparisonMatrix
            assert final_state["comparison"] is not None
            matrix: ComparisonMatrix = final_state["comparison"]
            assert isinstance(matrix, ComparisonMatrix)
            assert "Zoho" in matrix.entities
            assert "Freshworks" in matrix.entities
            assert len(matrix.cells) >= 2

            zoho_cell = matrix.get_cell("Zoho", "Pricing")
            assert zoho_cell is not None
            assert zoho_cell.trust_tag == TrustTag.GREEN

            # Render markdown table to prove it produces a table
            md_table = matrix.to_markdown_table()
            assert "| Zoho | Freshworks |" in md_table
            assert "🟢" in md_table
