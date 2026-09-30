"""LangGraph end-to-end research workflow connecting Planner and Parallel Researchers.

Specification: PRD.md Section 5 & TECH_SPEC.md Section 4.3 & AGENT_TASKS.md Task 12.
Workflow:
START -> Planner -> Parallel Researchers -> END
(Checker, Comparer, and Writer will be chained in subsequent phases).
"""

import logging
import uuid
from typing import Optional
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflow.parallel import ParallelResearcher, get_parallel_researcher
from app.workflow.planner import Planner, get_planner
from app.workflow.state import ResearchState, create_initial_research_state

logger = logging.getLogger("researchops.graph")


def create_research_graph(
    planner: Optional[Planner] = None,
    parallel_researcher: Optional[ParallelResearcher] = None,
) -> CompiledStateGraph:
    """Construct and compile the initial LangGraph research pipeline.

    Connects:
        START -> planner_node -> research_node -> END
    """
    _planner = planner or get_planner()
    _parallel_researcher = parallel_researcher or get_parallel_researcher()

    async def planner_node(state: ResearchState) -> dict:
        """Execute strategic planning to generate structured research jobs."""
        logger.info("[Workflow] Starting planner node for run %s", state["research_id"])
        plan = await _planner.plan(
            question=state["question"],
            research_run_id=state["research_id"],
        )
        return {
            "assumptions": plan.assumptions,
            "entities": plan.entities,
            "research_jobs": plan.research_jobs,
            "workflow_status": "planned",
        }

    async def research_node(state: ResearchState) -> dict:
        """Execute independent research jobs in parallel."""
        jobs = state.get("research_jobs", [])
        logger.info("[Workflow] Starting parallel research node for %d jobs", len(jobs))
        batch = await _parallel_researcher.execute_jobs(jobs)
        return {
            "research_jobs": batch.jobs,
            "facts": batch.facts,
            "sources": batch.sources,
            "workflow_status": "researched",
        }

    builder = StateGraph(ResearchState)
    builder.add_node("planner", planner_node)
    builder.add_node("parallel_research", research_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "parallel_research")
    builder.add_edge("parallel_research", END)

    return builder.compile()


async def run_research_pipeline(
    question: str,
    research_id: Optional[str] = None,
    planner: Optional[Planner] = None,
    parallel_researcher: Optional[ParallelResearcher] = None,
) -> ResearchState:
    """Execute the end-to-end research pipeline for a given business question.

    Args:
        question: Natural language research query.
        research_id: Optional unique run identifier (generated if omitted).
        planner: Optional custom Planner instance.
        parallel_researcher: Optional custom ParallelResearcher instance.

    Returns:
        The final populated ResearchState containing jobs, facts, and sources.
    """
    run_id = research_id or f"run-{uuid.uuid4().hex[:12]}"
    initial_state = create_initial_research_state(run_id, question)

    graph = create_research_graph(planner=planner, parallel_researcher=parallel_researcher)
    logger.info("Executing research graph for question: '%s' (Run ID: %s)", question, run_id)

    final_state: ResearchState = await graph.ainvoke(initial_state)
    logger.info(
        "Research graph finished (Run ID: %s, Status: %s): %d jobs, %d facts, %d sources",
        run_id,
        final_state.get("workflow_status"),
        len(final_state.get("research_jobs", [])),
        len(final_state.get("facts", [])),
        len(final_state.get("sources", [])),
    )
    return final_state
