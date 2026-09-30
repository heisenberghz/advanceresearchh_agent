"""External integrations package for ResearchOps."""

from app.integrations.openrouter import OpenRouterClient, get_openrouter_client

__all__ = ["OpenRouterClient", "get_openrouter_client"]
