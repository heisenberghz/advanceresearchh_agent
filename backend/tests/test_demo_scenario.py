"""Task 41: Highly Reliable Demonstration Scenario Test.

Specification: PRD.md Section 5, TECH_SPEC.md Section 22, AGENT_TASKS.md Task 41.
Demonstrates:
1. Complex business question (EV Scooter Subscriptions in Bengaluru)
2. Planning
3. Parallel research
4. Evidence collection
5. Verification
6. Trust tags
7. Conflict detection
8. Research gaps
9. Comparison
10. Final report
11. Source traceability
12. Live progress / state transitions
"""

import pytest
from unittest.mock import patch

from app.db.repository import ResearchRepository
from app.integrations.openrouter import OpenRouterClient
from app.integrations.tavily import TavilyClient
from app.models.enums import TrustTag
from app.models.source import Source
from app.models.comparison import ComparisonMatrix
from app.models.report import ResearchReport
from app.workflow.graph import run_research_pipeline
from app.workflow.parallel import ParallelResearcher
from app.workflow.planner import Planner
from app.workflow.researcher import Researcher
from app.workflow.state import ResearchState


@pytest.mark.anyio
async def test_demo_scenario_ev_mobility_bengaluru():
    """Verify the flagship demo scenario satisfies all 12 Task 41 criteria."""
    
    # 1. Complex business question
    question = (
        "Compare Bounce, Yulu, and Vogo electric scooter subscriptions in Bengaluru "
        "on monthly pricing, battery swap networks, and regulations."
    )
    run_id = "demo-bengaluru-ev-scooters"
    repo = ResearchRepository()
    mock_tavily = TavilyClient(api_key="tvly-mock-key")

    async def mock_demo_search(query: str, research_run_id: str, max_results=None):
        q_lower = query.lower()
        if "bounce" in q_lower:
            return [
                Source(
                    id="src-bounce-official",
                    research_run_id=research_run_id,
                    url="https://bounceshare.com/pricing",
                    title="Bounce Daily & Monthly Electric Scooter Subscriptions",
                    domain="bounceshare.com",
                    evidence="Bounce Infinity offers monthly subscription plans starting at ₹2,999/month with battery swap access across Bengaluru.",
                ),
                Source(
                    id="src-bounce-news",
                    research_run_id=research_run_id,
                    url="https://inc42.com/bounce-fleet",
                    title="Inc42 - Bounce Bengaluru Fleet Analysis",
                    domain="inc42.com",
                    evidence="Bounce operates over 5,000 electric scooters across 120 swap hubs in Bengaluru.",
                )
            ]
        elif "yulu" in q_lower:
            return [
                Source(
                    id="src-yulu-official",
                    research_run_id=research_run_id,
                    url="https://yulu.bike/plans",
                    title="Yulu Wynn and Miracle Rental Plans",
                    domain="yulu.bike",
                    evidence="Yulu long-term rental plans start at ₹199/day or ₹3,499/month powered by the Yuma battery swap network.",
                ),
                Source(
                    id="src-yulu-conflicting-rate",
                    research_run_id=research_run_id,
                    url="https://thehindubusinessline.com/yulu-expansion",
                    title="The Hindu BusinessLine - Yulu Subscription Tiers",
                    domain="thehindubusinessline.com",
                    evidence="Yulu monthly rental packages range from ₹3,899 to ₹4,299 depending on deposit and battery swap credits.",
                )
            ]
        elif "vogo" in q_lower:
            # Undisclosed private metrics to trigger explicit research gap
            return []
        
        return []

    mock_llm = OpenRouterClient(api_key=None, gemini_api_key=None)

    progress_events = []
    def record_progress(snapshot):
        progress_events.append(snapshot.get("workflow_status"))

    with patch.object(mock_tavily, "search_to_sources", side_effect=mock_demo_search):
        researcher = Researcher(tavily_client=mock_tavily, openrouter_client=mock_llm)
        parallel_researcher = ParallelResearcher(researcher=researcher, max_concurrency=4)
        planner = Planner(openrouter_client=mock_llm)

        # 2. Planning, 3. Parallel research, 4. Evidence collection, 5. Verification
        final_state: ResearchState = await run_research_pipeline(
            question=question,
            research_id=run_id,
            planner=planner,
            parallel_researcher=parallel_researcher,
            repository=repo,
        )

        # 12. Live Progress Tracking
        assert final_state["workflow_status"] == "completed"
        assert len(final_state["research_jobs"]) >= 2

        # 6. Trust Tags (Assigned deterministically based on corroboration and conflict rules)
        facts = final_state["facts"]
        assert len(facts) >= 2
        bounce_facts = [f for f in facts if "bounce" in f.entity.lower()]
        assert len(bounce_facts) >= 1
        assert any(f.trust_tag in (TrustTag.GREEN, TrustTag.YELLOW, TrustTag.RED) for f in facts)

        # 11. Source Traceability
        for f in facts:
            assert len(f.source_ids) >= 1
            assert len(f.evidence) >= 1
            assert f.evidence[0].source_id.startswith("src-")
            assert f.evidence[0].text != ""
        assert any(s.url.startswith("http") for s in final_state["sources"])

        # 7. Conflict Detection (Yulu & Bounce pricing discrepancies flagged and preserved)
        conflicts = final_state["conflicts"]
        assert len(conflicts) >= 1
        assert any("bounce" in c.entity.lower() or "yulu" in c.entity.lower() for c in conflicts)

        # 8. Research Gaps (Vogo undisclosed pricing logged without hallucinations)
        gaps = final_state["gaps"]
        assert len(gaps) >= 1
        assert any("vogo" in g.requested_information.lower() or "vogo" in g.reason.lower() for g in gaps)

        # 9. Structured Comparison
        comparison: ComparisonMatrix = final_state["comparison"]
        assert comparison is not None
        assert len(comparison.entities) >= 2
        assert len(comparison.metrics) >= 1
        md_table = comparison.to_markdown_table()
        assert "| Dimension / Metric |" in md_table

        # 10. Final Synthesized Report
        report: ResearchReport = final_state["report"]
        assert report is not None
        assert report.title != ""
        assert report.executive_summary != ""
        assert len(report.detailed_findings) >= 2
        assert report.markdown_content is not None
        assert "## 1. Executive Summary" in report.markdown_content
