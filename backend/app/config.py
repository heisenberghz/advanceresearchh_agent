"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # External API Keys (kept strictly server-side)
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    # Supabase PostgreSQL Configuration
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")

    # Model Configuration
    research_model: str = Field(default="deepseek/deepseek-chat", alias="RESEARCH_MODEL")
    writer_model: str = Field(default="anthropic/claude-3.5-sonnet", alias="WRITER_MODEL")

    # Workflow Boundaries & Cost Limits
    max_research_retries: int = Field(default=2, alias="MAX_RESEARCH_RETRIES", ge=0, le=5)
    max_searches_per_job: int = Field(default=3, alias="MAX_SEARCHES_PER_JOB", ge=1, le=10)

    # Server Settings
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    port: int = Field(default=8000, alias="PORT")

    def check_missing_required_keys(self) -> list[str]:
        """Check for external API keys required for live research execution."""
        missing = []
        if not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")
        return missing

    def ensure_research_configured(self) -> None:
        """Raise an error if required configuration for research is missing."""
        missing = self.check_missing_required_keys()
        if missing:
            raise ValueError(
                f"Missing required configuration for research execution: {', '.join(missing)}. "
                "Please configure them in your backend/.env file."
            )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
