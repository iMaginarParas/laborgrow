from config.settings import settings
from supabase import create_client, Client
import os

# Initialize Supabase Client
# We use the Service Role Key for backend operations to bypass RLS when needed
# or the Anon key if only public access is required.
supabase_url = settings.SUPABASE_URL
supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY

if not supabase_url or not supabase_key:
    # Fallback to env for cases where settings might not be fully loaded
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None

async def get_supabase() -> Client:
    """
    FastAPI dependency yielding the Supabase client.
    """
    if not supabase:
        raise Exception("Supabase client is not initialized. Check your environment variables.")
    return supabase

