"""ResearchRun domain model representing a full research investigation."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.enums import RunStatus


class ResearchRun(BaseModel):
    """The overarching research lifecycle from user question to report."""

    id: str = Field(description="Unique research run ID")
    question: str = Field(description="Original natural-language business question")
    status: RunStatus = Field(default=RunStatus.PENDING, description="Current workflow state")
    assumptions: List[str] = Field(default_factory=list, description="Scoping assumptions")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Run initiation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Run completion timestamp",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or len(v.strip()) < 5:
            raise ValueError("Research question must be at least 5 characters long")
        return v.strip()
