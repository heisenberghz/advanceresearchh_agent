"""Report domain models representing the final synthesized research deliverable."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.fact import Fact
from app.models.source import Source
from app.models.conflict import Conflict
from app.models.gap import ResearchGap
from app.models.comparison import ComparisonMatrix


class ResearchReport(BaseModel):
    """The final synthesized research deliverable produced by the Writer."""

    id: str = Field(description="Unique report identifier")
    research_run_id: str = Field(description="Associated research run ID")
    title: str = Field(description="Report title summarizing the research question")
    executive_summary: str = Field(description="High-level synthesis of findings")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made by Planner")
    comparison: Optional[ComparisonMatrix] = Field(default=None, description="Structured matrix comparison")
    key_findings: List[str] = Field(default_factory=list, description="Primary takeaways")
    detailed_findings: List[Fact] = Field(default_factory=list, description="Verified facts and evidence")
    conflicting_information: List[Conflict] = Field(default_factory=list, description="Explicit contradictory sources")
    research_gaps: List[ResearchGap] = Field(default_factory=list, description="Gaps that could not be verified")
    sources: List[Source] = Field(default_factory=list, description="Full bibliography of cited sources")
    markdown_content: Optional[str] = Field(default=None, description="Full rendered Markdown content")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    def to_markdown(self) -> str:
        """Format the report into a complete GitHub-Flavored Markdown document."""
        sections = [
            f"# {self.title}\n",
            f"**Research Run ID:** `{self.research_run_id}` | **Generated:** {self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
            "## 1. Executive Summary\n",
            self.executive_summary + "\n",
            "## 2. Research Scope & Assumptions\n",
        ]

        if self.assumptions:
            for asm in self.assumptions:
                sections.append(f"- {asm}")
        else:
            sections.append("No specific scoping assumptions declared.")
        sections.append("\n## 3. Comparison\n")

        if self.comparison:
            sections.append(self.comparison.to_markdown_table() + "\n")
        else:
            sections.append("No comparison matrix available.\n")

        sections.append("## 4. Key Findings\n")
        if self.key_findings:
            for kf in self.key_findings:
                sections.append(f"- {kf}")
        else:
            sections.append("No specific key findings recorded.")
        sections.append("\n## 5. Detailed Findings\n")

        # Group facts by entity
        facts_by_entity: dict[str, list[Fact]] = {}
        for f in self.detailed_findings:
            facts_by_entity.setdefault(f.entity, []).append(f)

        if facts_by_entity:
            for entity, e_facts in facts_by_entity.items():
                sections.append(f"### {entity}")
                for f in e_facts:
                    tag_str = f.trust_tag.value if hasattr(f.trust_tag, "value") else str(f.trust_tag)
                    badge = "🟢" if tag_str.upper() == "GREEN" else "🟡" if tag_str.upper() == "YELLOW" else "🔴"
                    ev_snippet = f.evidence[0].text if f.evidence else "No excerpt available."
                    sections.append(f"- **{f.attribute}:** {badge} {f.value}")
                    sections.append(f"  - *Evidence:* \"{ev_snippet}\"")
                    if f.source_ids:
                        sections.append(f"  - *Sources:* {', '.join(f'`{sid}`' for sid in f.source_ids)}")
                sections.append("")
        else:
            sections.append("No detailed facts recorded.\n")

        sections.append("## 6. Conflicting Information\n")
        if self.conflicting_information:
            for conf in self.conflicting_information:
                sections.append(f"### Conflict: {conf.description}")
                status_str = conf.status.value.upper() if hasattr(conf.status, "value") else str(conf.status)
                sections.append(f"- **Status:** {status_str}")
                if hasattr(conf, "resolution_note") and conf.resolution_note:
                    sections.append(f"- **Note:** {conf.resolution_note}")
                sections.append("- **Competing Claims:**")
                for comp in conf.competing_values:
                    sections.append(f"  - Value: `{comp.value}` | Source: {comp.source_url}")
                    sections.append(f"    - *Snippet:* \"{comp.evidence}\"")
                sections.append("")
        else:
            sections.append("No significant factual conflicts detected across verified sources.\n")

        sections.append("## 7. Research Gaps\n")
        if self.research_gaps:
            for gap in self.research_gaps:
                sections.append(f"- **{gap.requested_information}** ({gap.attempts} attempt{'s' if gap.attempts > 1 else ''}): {gap.reason}")
        else:
            sections.append("No research gaps identified; all requested information was successfully verified.\n")

        sections.append("\n## 8. Sources & Citations\n")
        if self.sources:
            for idx, s in enumerate(self.sources, 1):
                domain_part = f" ({s.domain})" if s.domain else ""
                title_part = s.title or s.url
                retrieved_str = s.retrieved_at.strftime("%Y-%m-%d %H:%M UTC") if s.retrieved_at else "N/A"
                sections.append(f"{idx}. [{title_part}]({s.url}){domain_part} - Retrieved: {retrieved_str}")
        else:
            sections.append("No sources recorded.")

        return "\n".join(sections)
