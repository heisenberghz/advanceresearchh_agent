"""Conflict models representing contradictory research evidence."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.enums import ConflictStatus


class CompetingValue(BaseModel):
    """An individual value claim with its citing source."""

    value: str = Field(description="The contradictory value reported")
    source_id: Optional[str] = Field(default=None, description="Referenced source record ID")
    source_url: Optional[str] = Field(default=None, description="URL of reporting page")
    evidence: Optional[str] = Field(default=None, description="Snippet or quote asserting this value")


class Conflict(BaseModel):
    """Explicit record of conflicting information between multiple sources."""

    id: str = Field(description="Unique conflict identifier")
    research_run_id: str = Field(description="Associated research run ID")
    description: str = Field(description="Summary of the contradiction")
    status: ConflictStatus = Field(default=ConflictStatus.UNRESOLVED, description="Resolution status")
    competing_values: List[CompetingValue] = Field(
        min_length=2,
        description="At least two opposing values must be preserved",
    )
    supporting_sources: List[str] = Field(
        default_factory=list,
        description="IDs of all sources involved in the conflict",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Conflict registration timestamp",
    )
