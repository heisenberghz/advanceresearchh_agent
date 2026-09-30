"""LangGraph end-to-end research workflow connecting Planner, Parallel Researchers, Checker, and Retry Loop.

Specification: PRD.md Section 5, TECH_SPEC.md Sections 4.3 & 16, AGENT_TASKS.md Task 12 & 16.
Workflow:
START -> Planner -> Parallel Research -> Checker -> [Conditional Retry Loop] -> END
"""

import logging
from typing import Optional
import uuid
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflow.checker import Checker, get_checker
from app.workflow.comparer import Comparer, get_comparer
from app.workflow.gaps import GapDetector, get_gap_detector
from app.workflow.parallel import ParallelResearcher, get_parallel_researcher
from app.workflow.planner import Planner, get_planner
from app.workflow.retry import RetryCoordinator, get_retry_coordinator
from app.workflow.state import ResearchState, create_initial_research_state

logger = logging.getLogger("researchops.graph")


def create_research_graph(
    planner: Optional[Planner] = None,
    parallel_researcher: Optional[ParallelResearcher] = None,
    checker: Optional[Checker] = None,
    retry_coordinator: Optional[RetryCoordinator] = None,
    gap_detector: Optional[GapDetector] = None,
    comparer: Optional[Comparer] = None,
) -> CompiledStateGraph:
    """Construct and compile the LangGraph research pipeline with Checker, Retry Loop, Gaps, and Comparer.

    Connects:
        START -> planner -> parallel_research -> checker
        checker -> [should_retry?]
            YES -> retry_research -> checker (loop)
            NO  -> detect_gaps -> comparer -> END
    """
    _planner = planner or get_planner()
    _parallel_researcher = parallel_researcher or get_parallel_researcher()
    _checker = checker or get_checker()
    _retry_coordinator = retry_coordinator or get_retry_coordinator(parallel_researcher=_parallel_researcher)
    _gap_detector = gap_detector or get_gap_detector()
    _comparer = comparer or get_comparer()

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

    async def checker_node(state: ResearchState) -> dict:
        """Independently verify facts against sources, calculate trust, and detect conflicts."""
        facts = state.get("facts", [])
        sources = state.get("sources", [])
        run_id = state.get("research_id", "run-default")
        logger.info("[Workflow] Starting checker node for %d facts, %d sources", len(facts), len(sources))
        batch = _checker.check_all(facts, sources, run_id)
        return {
            "facts": batch.facts,
            "verification_results": batch.verification_results,
            "conflicts": batch.conflicts,
            "workflow_status": "checked",
        }

    async def retry_node(state: ResearchState) -> dict:
        """Selectively re-research jobs with weak, ungrounded, or failing evidence."""
        candidates = _retry_coordinator.identify_retry_candidates(state)
        logger.info("[Workflow] Starting retry node for %d candidates", len(candidates))
        batch, updated_retry_counts = await _retry_coordinator.execute_retries(
            candidates,
            state.get("retry_counts", {}),
        )
        return {
            "research_jobs": batch.jobs,
            "facts": batch.facts,
            "sources": batch.sources,
            "retry_counts": updated_retry_counts,
            "workflow_status": "retrying",
        }

    async def gaps_node(state: ResearchState) -> dict:
        """Detect and persist information gaps for topics that could not be reliably verified."""
        logger.info("[Workflow] Starting gap detection node for run %s", state["research_id"])
        detected_gaps = _gap_detector.detect_gaps(state)
        _gap_detector.persist_gaps(detected_gaps)
        return {
            "gaps": detected_gaps,
            "workflow_status": "checked",
        }

    async def comparer_node(state: ResearchState) -> dict:
        """Construct structured side-by-side comparison matrix from verified facts and gaps."""
        logger.info("[Workflow] Starting comparer node for run %s", state["research_id"])
        matrix = _comparer.compare(state)
        return {
            "comparison": matrix,
            "workflow_status": "compared",
        }

    def route_after_checker(state: ResearchState) -> str:
        """Deterministic conditional router deciding between retry loop and gap detection."""
        if _retry_coordinator.should_retry(state):
            logger.info("[Workflow] Weak evidence detected; routing to retry_research")
            return "retry_research"
        logger.info("[Workflow] Evidence sufficient or retry limits reached; proceeding to detect_gaps")
        return "detect_gaps"

    builder = StateGraph(ResearchState)
    builder.add_node("planner", planner_node)
    builder.add_node("parallel_research", research_node)
    builder.add_node("checker", checker_node)
    builder.add_node("retry_research", retry_node)
    builder.add_node("detect_gaps", gaps_node)
    builder.add_node("comparer", comparer_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "parallel_research")
    builder.add_edge("parallel_research", "checker")
    builder.add_conditional_edges(
        "checker",
        route_after_checker,
        {
            "retry_research": "retry_research",
            "detect_gaps": "detect_gaps",
        },
    )
    builder.add_edge("retry_research", "checker")
    builder.add_edge("detect_gaps", "comparer")
    builder.add_edge("comparer", END)

    return builder.compile()


async def run_research_pipeline(
    question: str,
    research_id: Optional[str] = None,
    planner: Optional[Planner] = None,
    parallel_researcher: Optional[ParallelResearcher] = None,
    checker: Optional[Checker] = None,
    retry_coordinator: Optional[RetryCoordinator] = None,
    gap_detector: Optional[GapDetector] = None,
    comparer: Optional[Comparer] = None,
) -> ResearchState:
    """Execute the end-to-end research pipeline for a given business question.

    Args:
        question: Natural language research query.
        research_id: Optional unique run identifier (generated if omitted).
        planner: Optional custom Planner instance.
        parallel_researcher: Optional custom ParallelResearcher instance.
        checker: Optional custom Checker instance.
        retry_coordinator: Optional custom RetryCoordinator instance.
        gap_detector: Optional custom GapDetector instance.
        comparer: Optional custom Comparer instance.

    Returns:
        The final populated ResearchState containing verified jobs, facts, sources, gaps, and comparison.
    """
    run_id = research_id or f"run-{uuid.uuid4().hex[:12]}"
    initial_state = create_initial_research_state(run_id, question)

    graph = create_research_graph(
        planner=planner,
        parallel_researcher=parallel_researcher,
        checker=checker,
        retry_coordinator=retry_coordinator,
        gap_detector=gap_detector,
        comparer=comparer,
    )
    logger.info("Executing research graph for question: '%s' (Run ID: %s)", question, run_id)

    final_state: ResearchState = await graph.ainvoke(initial_state)
    logger.info(
        "Research graph finished (Run ID: %s, Status: %s): %d jobs, %d facts, %d sources, %d verification results, %d conflicts, %d gaps, comparison matrix %s",
        run_id,
        final_state.get("workflow_status"),
        len(final_state.get("research_jobs", [])),
        len(final_state.get("facts", [])),
        len(final_state.get("sources", [])),
        len(final_state.get("verification_results", [])),
        len(final_state.get("conflicts", [])),
        len(final_state.get("gaps", [])),
        "present" if final_state.get("comparison") is not None else "absent",
    )
    return final_state

