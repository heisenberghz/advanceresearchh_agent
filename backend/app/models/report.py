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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
