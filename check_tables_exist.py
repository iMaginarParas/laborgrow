import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    response = supabase.table("messages").select("*").limit(1).execute()
    print("Messages table exists.")
except Exception as e:
    print(f"Messages table check failed: {e}")

try:
    response = supabase.table("notifications").select("*").limit(1).execute()
    print("Notifications table exists.")
except Exception as e:
    print(f"Notifications table check failed: {e}")
