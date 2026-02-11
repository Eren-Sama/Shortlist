"""
Shortlist — Supabase Database Client

Async Supabase client for FastAPI integration.
Handles connection lifecycle and provides dependency injection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from supabase import acreate_client, AsyncClient

from app.config import get_settings

# Module-level client reference — initialized during app lifespan
_supabase_client: Optional[AsyncClient] = None


async def init_supabase() -> AsyncClient:
    """
    Initialize the async Supabase client.
    Called once during application startup.
    Uses the SERVICE_KEY for server-side operations.
    """
    global _supabase_client

    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set. "
            "Check your .env file."
        )

    _supabase_client = await acreate_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY,
    )

    return _supabase_client


async def close_supabase() -> None:
    """
    Cleanup Supabase client on shutdown.
    """
    global _supabase_client
    # supabase-py async client doesn't have explicit close,
    # but we clear the reference for clean shutdown
    _supabase_client = None


def get_supabase() -> AsyncClient:
    """
    Dependency injection for route handlers.
    Returns the initialized Supabase client.

    Usage:
        @router.get("/data")
        async def get_data(db: AsyncClient = Depends(get_supabase)):
            result = await db.table("table").select("*").execute()
    """
    if _supabase_client is None:
        raise RuntimeError(
            "Supabase client not initialized. "
            "Ensure init_supabase() was called during startup."
        )
    return _supabase_client
