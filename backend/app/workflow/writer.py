"""Writer module generating the final synthesized research report with traceable provenance.

Specification: PRD.md Section 5.5, TECH_SPEC.md Section 21 & 22, and AGENT_TASKS.md Task 19.
Key invariants:
- Contains all 8 mandatory sections:
  1. Executive Summary
  2. Research Scope & Assumptions
  3. Comparison
  4. Key Findings
  5. Detailed Findings
  6. Conflicting Information
  7. Research Gaps
  8. Sources & Citations
- Uses only information present in the verified research state.
- Never invents or hallucinates facts absent from research findings.
- Explicitly distinguishes established findings, uncertain claims, conflicts, and gaps.
- Preserves 100% provenance and source citations.
- Persists report to database repository.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.db.repository import ResearchRepository, get_repository
from app.integrations.openrouter import OpenRouterClient
from app.models.comparison import ComparisonMatrix
from app.models.enums import TrustTag
from app.models.fact import Fact
from app.models.report import ResearchReport
from app.workflow.comparer import Comparer, get_comparer
from app.workflow.state import ResearchState

logger = logging.getLogger("researchops.writer")


class StructuredExecutiveSynthesis(BaseModel):
    """Structured response model for LLM report synthesis."""

    title: str = Field(description="Clear, descriptive report title")
    executive_summary: str = Field(description="Comprehensive executive summary summarizing findings, comparisons, and gaps")
    key_findings: List[str] = Field(description="3-6 bulleted strategic key findings")


WRITER_SYSTEM_PROMPT = """You are the Lead Research Analyst for ResearchOps: The Autonomous Research Agent.
Your job is to synthesize an objective, authoritative executive summary and key findings based STRICTLY on verified research findings, structured comparisons, detected conflicts, and identified research gaps.

CRITICAL INVARIANTS:
1. Grounding: NEVER invent or hallucinate facts, metrics, or citations absent from the input.
2. Gaps: Explicitly acknowledge missing or unverified information (gaps) as research limitations.
3. Conflicts: Note any conflicting figures or contradictory disclosures.
4. Tone: Professional, analytical, concise, and business-focused.
"""


class Writer:
    """Synthesizes comprehensive, auditable research reports from verified findings."""

    def __init__(
        self,
        openrouter_client: Optional[OpenRouterClient] = None,
        repository: Optional[ResearchRepository] = None,
        comparer: Optional[Comparer] = None,
    ) -> None:
        self.openrouter_client = openrouter_client
        self.repository = repository or get_repository()
        self.comparer = comparer or get_comparer()

    async def generate_report(self, state: ResearchState) -> ResearchReport:
        """Synthesize the complete ResearchReport from the verified ResearchState."""
        run_id = state.get("research_id", "run-default")
        question = state.get("question", "Research Analysis")
        assumptions = state.get("assumptions", [])
        entities = state.get("entities", [])
        facts = state.get("facts", [])
        conflicts = state.get("conflicts", [])
        gaps = state.get("gaps", [])
        sources = state.get("sources", [])

        # Ensure comparison matrix is available
        comparison: Optional[ComparisonMatrix] = state.get("comparison")
        if comparison is None:
            comparison = self.comparer.compare(state)

        # Attempt structured synthesis via OpenRouter if configured
        title, executive_summary, key_findings = await self._synthesize_narrative(
            question=question,
            assumptions=assumptions,
            entities=entities,
            facts=facts,
            conflicts=conflicts,
            gaps=gaps,
            comparison=comparison,
        )

        report = ResearchReport(
            id=f"rep-{run_id[:8]}",
            research_run_id=run_id,
            title=title,
            executive_summary=executive_summary,
            assumptions=assumptions,
            comparison=comparison,
            key_findings=key_findings,
            detailed_findings=facts,
            conflicting_information=conflicts,
            research_gaps=gaps,
            sources=sources,
        )
        report.markdown_content = report.to_markdown()

        # Persist report
        self.persist_report(report)
        logger.info(
            "[Writer] Generated ResearchReport '%s' for run %s with %d findings, %d gaps, %d conflicts",
            report.title,
            run_id,
            len(facts),
            len(gaps),
            len(conflicts),
        )
        return report

    async def _synthesize_narrative(
        self,
        question: str,
        assumptions: List[str],
        entities: List[str],
        facts: List[Fact],
        conflicts: List[Any],
        gaps: List[Any],
        comparison: ComparisonMatrix,
    ) -> tuple[str, str, List[str]]:
        """Synthesize report title, executive summary, and key findings using LLM with deterministic fallback."""
        if self.openrouter_client and self.openrouter_client.is_configured:
            try:
                # Build context for LLM synthesis
                facts_summary = "\n".join(
                    f"- {f.entity} {f.attribute}: {f.value} (Trust: {f.trust_tag.value})"
                    for f in facts
                ) or "No verified facts."
                conflicts_summary = "\n".join(
                    f"- {c.description} (Status: {getattr(c.status, 'value', c.status)})"
                    for c in conflicts
                ) or "None."
                gaps_summary = "\n".join(
                    f"- {g.requested_information}: {g.reason}"
                    for g in gaps
                ) or "None."
                table_md = comparison.to_markdown_table()

                user_prompt = f"""Synthesize the executive narrative for the following research inquiry:
Research Question: {question}
Assumptions: {', '.join(assumptions) if assumptions else 'None'}
Entities: {', '.join(entities) if entities else 'None'}

Comparison Table:
{table_md}

Verified Facts:
{facts_summary}

Detected Conflicts:
{conflicts_summary}

Identified Research Gaps:
{gaps_summary}
"""
                messages = [
                    {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]

                synthesis = await self.openrouter_client.chat_structured(
                    messages=messages,
                    response_model=StructuredExecutiveSynthesis,
                    model=self.openrouter_client.writer_model,
                )
                logger.info("[Writer] Successfully synthesized narrative via OpenRouter.")
                return synthesis.title, synthesis.executive_summary, synthesis.key_findings

            except Exception as exc:
                logger.warning(
                    "[Writer] OpenRouter narrative synthesis failed or unconfigured (%s); using deterministic synthesis.",
                    str(exc),
                )

        # Deterministic Structured Fallback Synthesis
        return self._deterministic_synthesis(
            question=question,
            entities=entities,
            facts=facts,
            conflicts=conflicts,
            gaps=gaps,
        )

    def _deterministic_synthesis(
        self,
        question: str,
        entities: List[str],
        facts: List[Fact],
        conflicts: List[Any],
        gaps: List[Any],
    ) -> tuple[str, str, List[str]]:
        """Construct deterministic, factually grounded narrative when LLM is unavailable."""
        title = f"Competitive Research Report: {question}"
        entity_str = ", ".join(entities) if entities else "target market entities"

        verified_facts = [f for f in facts if f.trust_tag in (TrustTag.GREEN, TrustTag.YELLOW)]
        green_facts = [f for f in facts if f.trust_tag == TrustTag.GREEN]

        exec_parts = [
            f"This research report evaluates {entity_str} in response to the inquiry: \"{question}\".",
            f"A total of {len(verified_facts)} metric disclosures were verified across retrieved documentation, "
            f"including {len(green_facts)} high-confidence findings supported by official or corroborated sources.",
        ]

        if conflicts:
            exec_parts.append(
                f"Additionally, {len(conflicts)} factual conflict was identified across public sources and preserved "
                f"for comparative evaluation."
            )
        if gaps:
            exec_parts.append(
                f"{len(gaps)} research gap(s) were explicitly recorded where reliable public information could not be "
                f"independently established."
            )

        executive_summary = " ".join(exec_parts)

        # Key findings
        key_findings: List[str] = []
        for ent in entities:
            ent_facts = [f for f in verified_facts if f.entity.lower() == ent.lower()]
            if ent_facts:
                top_items = "; ".join(f"{f.attribute}: {f.value}" for f in ent_facts[:2])
                key_findings.append(f"{ent}: Verified data indicates {top_items}.")

        if conflicts:
            key_findings.append(
                f"Factual Conflicts: {len(conflicts)} metric discrepancy detected across reporting sources."
            )
        if gaps:
            gap_topics = ", ".join(g.requested_information for g in gaps[:3])
            key_findings.append(
                f"Research Gaps: Information on {gap_topics} could not be established from public filings."
            )

        if not key_findings:
            key_findings.append("Research completed with verified factual findings recorded in the comparison table.")

        return title, executive_summary, key_findings

    def persist_report(self, report: ResearchReport) -> ResearchReport:
        """Persist report to repository."""
        try:
            rep_dict = report.model_dump()
            rep_dict["created_at"] = report.created_at.isoformat()
            rep_dict["updated_at"] = report.updated_at.isoformat()
            self.repository.save_report(rep_dict)
        except Exception as exc:
            logger.error("Failed to persist report %s: %s", report.id, str(exc))
        return report


_WRITER_INSTANCE: Optional[Writer] = None


def get_writer(
    openrouter_client: Optional[OpenRouterClient] = None,
    repository: Optional[ResearchRepository] = None,
    comparer: Optional[Comparer] = None,
) -> Writer:
    """Retrieve or initialize the Writer singleton instance."""
    global _WRITER_INSTANCE
    if _WRITER_INSTANCE is None or openrouter_client is not None or repository is not None:
        _WRITER_INSTANCE = Writer(
            openrouter_client=openrouter_client,
            repository=repository,
            comparer=comparer,
        )
    return _WRITER_INSTANCE
