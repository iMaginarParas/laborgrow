import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
admin_supabase = create_client(SUPABASE_URL, SERVICE_KEY)

users = admin_supabase.auth.admin.list_users()
for user in users:
    print(f"EMAIL: {user.email}")
    print(f"PHONE: {user.phone}")
    print(f"ID:    {user.id}")
    print("-" * 20)
