from config.settings import settings
from supabase import create_async_client, AsyncClient
import os

# Global singleton for the async client
supabase: AsyncClient = None

async def init_supabase():
    """
    Initialize the global async Supabase client.
    Called once during application startup.
    """
    global supabase
    if supabase:
        return supabase

    url = settings.SUPABASE_URL or os.environ.get("SUPABASE_URL")
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError("Supabase configuration missing (URL or Key)")

    supabase = await create_async_client(url, key)
    return supabase

async def get_supabase() -> AsyncClient:
    """
    FastAPI dependency yielding the Supabase client.
    Ensures the client is initialized.
    """
    if not supabase:
        await init_supabase()
    return supabase

