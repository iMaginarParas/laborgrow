import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

try:
    print("Checking tables...")
    # List of tables we expect
    tables = ["categories", "employees", "bookings", "jobs"]
    for table in tables:
        try:
            # We try a select with a limit of 0 to check if the table exists
            res = supabase.table(table).select("*", count="exact").limit(0).execute()
            print(f"✅ Table '{table}' exists (Row Count: {res.count if hasattr(res, 'count') else 'N/A'})")
        except Exception as e:
            if "not found" in str(e).lower() or "cache" in str(e).lower():
                print(f"❌ Table '{table}' DOES NOT EXIST")
            else:
                print(f"⚠️ Error checking table '{table}': {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
