import os
from supabase import create_client, Client
from config.settings import settings

# Global singleton — initialised once at startup
supabase: Client = None

def init_supabase() -> Client:
    """
    Initialise the global synchronous Supabase client.
    Called once during application startup via the lifespan event.
    Uses Service Role Key for privileged backend operations.
    """
    global supabase
    if supabase:
        return supabase

    url = settings.SUPABASE_URL or os.environ.get("SUPABASE_URL")
    key = (
        settings.SUPABASE_SERVICE_ROLE_KEY
        or settings.SUPABASE_KEY
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_KEY")
    )

    if not url or not key:
        raise RuntimeError("Supabase configuration missing (URL or Key). Check environment variables.")

    supabase = create_client(url, key)
    return supabase

def get_supabase() -> Client:
    """
    Returns the initialised Supabase client.
    Raises RuntimeError if init_supabase() has not been called yet.
    """
    if not supabase:
        # Fallback: initialise on first use in case startup hook was skipped
        return init_supabase()
    return supabase

