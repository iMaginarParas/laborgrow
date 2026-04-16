import os
from supabase import create_client, Client
from config.settings import settings
from core.logger import logger

# Global singleton — initialised once at startup
supabase: Client = None

def init_supabase() -> Client:
    """
    Initialise the global synchronous Supabase client.
    Called once during application startup via the lifespan event.
    Uses Service Role Key for privileged backend operations to bypass RLS.
    """
    global supabase
    if supabase:
        return supabase

    url = settings.SUPABASE_URL or os.environ.get("SUPABASE_URL")
    
    # Priority:
    # 1. Explicit Service Role Key (Settings or Env)
    # 2. General SUPABASE_KEY (which might be the Service Role Key)
    # 3. Fallback to Anon Key (less ideal for backend)
    
    service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    general_key = settings.SUPABASE_KEY or os.environ.get("SUPABASE_KEY")
    anon_key = settings.SUPABASE_ANON_KEY or os.environ.get("SUPABASE_ANON_KEY")

    key = service_role_key or general_key or anon_key

    if not url or not key:
        logger.error("Supabase configuration missing", url_present=bool(url), key_present=bool(key))
        raise RuntimeError("Supabase configuration missing (URL or Key). Check environment variables.")

    # Log key type (safety: only log first 10 chars)
    key_type = "SERVICE_ROLE" if (service_role_key or "service_role" in key.lower()) else "UNKNOWN/ANON"
    logger.info(f"Supabase client initialized with {key_type} key", url=url)

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

