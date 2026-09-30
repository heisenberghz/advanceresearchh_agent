"""Supabase database client manager and connection utilities."""

import logging
from typing import Optional
from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger("researchops.db")

_supabase_client: Optional[Client] = None


class DatabaseClient:
    """Wrapper around Supabase client with health check and error management."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def is_connected(self) -> bool:
        """Check if client instance is initialized."""
        return self._client is not None

    @property
    def raw_client(self) -> Client:
        """Get the underlying Supabase client or raise if unconfigured."""
        if not self._client:
            raise RuntimeError(
                "Supabase client is not configured. "
                "Ensure SUPABASE_URL and SUPABASE_KEY are set in backend/.env"
            )
        return self._client

    def ping(self) -> dict:
        """Perform a quick ping check to verify connectivity."""
        if not self._client:
            return {"connected": False, "reason": "Credentials not configured"}
        try:
            # Query the research_runs table with limit 0 to check connection and schema
            response = self._client.table("research_runs").select("id").limit(1).execute()
            return {"connected": True, "details": f"Success, rows returned: {len(response.data)}"}
        except Exception as exc:
            logger.warning("Supabase ping failed: %s", str(exc))
            return {"connected": False, "reason": str(exc)}


def get_supabase_client() -> DatabaseClient:
    """Get or initialize the global Supabase client instance."""
    global _supabase_client
    settings = get_settings()

    if _supabase_client is not None:
        return DatabaseClient(_supabase_client)

    if settings.supabase_url and settings.supabase_key:
        try:
            _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
            logger.info("Supabase client initialized successfully for URL: %s", settings.supabase_url)
            return DatabaseClient(_supabase_client)
        except Exception as exc:
            logger.error("Failed to initialize Supabase client: %s", str(exc))
            return DatabaseClient(None)

    logger.debug("Supabase URL or Key not set; running in unconfigured state.")
    return DatabaseClient(None)
