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


class ComparisonMatrix(BaseModel):
    """Structured comparison table across multiple entities and dimensions."""

    entities: List[str] = Field(description="Researched entities compared side-by-side")
    metrics: List[str] = Field(description="Compared attributes or metrics")
    cells: List[ComparisonCell] = Field(description="Matrix cells containing values and trust tags")
