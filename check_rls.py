import os
import asyncio
from supabase import create_client
from dotenv import load_dotenv

async def check_anon_access():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    
    print(f"Testing with ANON KEY: {anon_key[:15]}...")
    client = create_client(url, anon_key)
    
    try:
        res = client.table("admin_users").select("*").execute()
        print(f"ANON KEY results: {res.data}")
    except Exception as e:
        print(f"ANON KEY error: {e}")

if __name__ == "__main__":
    asyncio.run(check_anon_access())
