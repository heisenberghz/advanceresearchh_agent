"""ResearchJob model representing sub-tasks created by the Planner."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.models.enums import JobStatus


class ResearchJob(BaseModel):
    """Sub-task dispatched to researcher nodes."""

    id: str = Field(description="Unique job identifier")
    research_run_id: str = Field(description="Associated research run ID")
    description: str = Field(description="Goal of this sub-research task")
    entity: Optional[str] = Field(default=None, description="Target entity if job is entity-specific")
    attribute: Optional[str] = Field(default=None, description="Target attribute/metric if specific")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Execution status")
    attempts: int = Field(default=0, ge=0, description="Execution retry count")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Raw outputs or extracted items")
    error: Optional[str] = Field(default=None, description="Error message if job failed")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
