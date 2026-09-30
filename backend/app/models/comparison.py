"""Comparison domain models for entity-metric matrices."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.enums import TrustTag


class ComparisonCell(BaseModel):
    """An individual metric cell in the comparison matrix."""

    entity: str = Field(description="Company or product name")
    metric: str = Field(description="Compared dimension (e.g. Founded, Pricing, Size)")
    value: str = Field(description="Value or 'Not found'")
    trust_tag: TrustTag = Field(description="Trust badge for this cell")
    fact_id: Optional[str] = Field(default=None, description="Linked Fact ID")
    source_ids: List[str] = Field(default_factory=list, description="Linked Source IDs")
    gap_id: Optional[str] = Field(default=None, description="Linked ResearchGap ID if missing")
    notes: Optional[str] = Field(default=None, description="Additional context or conflict notes")


class ComparisonMatrix(BaseModel):
    """Structured comparison table across multiple entities and dimensions."""

    entities: List[str] = Field(description="Researched entities compared side-by-side")
    metrics: List[str] = Field(description="Compared attributes or metrics")
    cells: List[ComparisonCell] = Field(description="Matrix cells containing values and trust tags")

    def get_cell(self, entity: str, metric: str) -> Optional[ComparisonCell]:
        """Find a cell by entity and metric names (case-insensitive)."""
        e_low = entity.strip().lower()
        m_low = metric.strip().lower()
        for cell in self.cells:
            if cell.entity.strip().lower() == e_low and cell.metric.strip().lower() == m_low:
                return cell
        return None

    def to_markdown_table(self) -> str:
        """Render a GitHub-flavored Markdown comparison table with trust badges."""
        if not self.entities:
            return "No entities available for comparison."

        # Header
        headers = ["Dimension / Metric"] + self.entities
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"

        rows = [header_line, sep_line]
        for metric in self.metrics:
            row = [metric]
            for entity in self.entities:
                cell = self.get_cell(entity, metric)
                if cell:
                    badge = (
                        "🟢" if cell.trust_tag == TrustTag.GREEN
                        else "🟡" if cell.trust_tag == TrustTag.YELLOW
                        else "🔴"
                    )
                    row.append(f"{badge} {cell.value}")
                else:
                    row.append("🔴 Not found")
            rows.append("| " + " | ".join(row) + " |")

        return "\n".join(rows)
