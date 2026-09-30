"""Fact and VerificationResult domain models."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.enums import TrustTag, VerificationStatus
from app.models.source import Evidence


class Fact(BaseModel):
    """The fundamental atomic unit of research findings."""

    id: str = Field(description="Unique fact identifier")
    research_run_id: str = Field(description="Associated research run ID")
    entity: str = Field(description="Target entity (e.g. company, product, market)")
    attribute: str = Field(description="Metric or dimension (e.g. Founded, Pricing, Market Share)")
    value: str = Field(description="Extracted value (e.g. '1996', '₹1,500/user/mo')")
    normalized_value: Optional[str] = Field(default=None, description="Standardized form for comparisons")
    source_ids: List[str] = Field(default_factory=list, description="IDs of cited Source records")
    evidence: List[Evidence] = Field(default_factory=list, description="Direct supporting excerpts")
    published_at: Optional[datetime] = Field(default=None, description="Reported date of information")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNSUPPORTED,
        description="Verification outcome from Checker",
    )
    trust_tag: TrustTag = Field(
        default=TrustTag.RED,
        description="Deterministic trust level (GREEN, YELLOW, RED)",
    )
    verification_reason: Optional[str] = Field(
        default=None,
        description="Explanation for the assigned trust tag and status",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )


    @field_validator("entity", "attribute", "value")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


class VerificationResult(BaseModel):
    """Output of the Checker evaluating a single fact."""

    fact_id: str = Field(description="Target fact identifier")
    status: VerificationStatus = Field(description="Verification decision")
    trust_tag: TrustTag = Field(description="Deterministic trust classification")
    reason: str = Field(description="Clear explanation of the verification assessment")
    supporting_sources: List[str] = Field(default_factory=list, description="IDs of valid supporting sources")
    conflicts: List[str] = Field(default_factory=list, description="IDs of detected conflicting records if any")
