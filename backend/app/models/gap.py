"""ResearchGap domain model representing missing or unverified information."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class ResearchGap(BaseModel):
    """Explicit representation of information that could not be verified."""

    id: str = Field(description="Unique research gap identifier")
    research_run_id: str = Field(description="Associated research run ID")
    requested_information: str = Field(description="The entity attribute or topic that was sought")
    reason: str = Field(description="Explicit explanation of why information could not be verified")
    attempts: int = Field(default=1, ge=1, description="Number of search attempts made")
    status: str = Field(default="gap", description="Status tag")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Gap registration timestamp",
    )

    @field_validator("requested_information", "reason")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or blank")
        return v.strip()
