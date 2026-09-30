"""Source and Evidence models."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Evidence(BaseModel):
    """Specific excerpt or text snippet from a source that supports a claim."""

    source_id: str = Field(description="ID of the supporting source document")
    text: str = Field(description="Verbatim excerpt or evidence passage from the source")
    location: Optional[str] = Field(default=None, description="Heading, paragraph, or section context")
    relevance: Optional[str] = Field(default=None, description="Brief note on how this text supports the fact")

    @field_validator("text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Evidence text snippet cannot be empty")
        return v.strip()


class Source(BaseModel):
    """Web source discovered and cited during research."""

    id: str = Field(description="Unique source identifier")
    research_run_id: str = Field(description="Associated research run ID")
    url: str = Field(description="Target webpage URL")
    title: Optional[str] = Field(default=None, description="Page or article title")
    domain: Optional[str] = Field(default=None, description="Extracted domain (e.g. techcrunch.com)")
    publisher: Optional[str] = Field(default=None, description="Publisher or organization name")
    published_at: Optional[datetime] = Field(default=None, description="Original publication timestamp if available")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the content was scraped/retrieved",
    )
    evidence: Optional[str] = Field(default=None, description="General snippet or extracted passage from search")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.startswith(("http://", "https://")):
            raise ValueError("Source URL must be a valid HTTP or HTTPS address")
        return v.strip()
