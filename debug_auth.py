import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Trying to sign in with a test user to see 401 message...")
    # Register a test user
    test_email = "test401_error@laborgro.com"
    test_password = "Password123!"
    
    print("Signing up test user...")
    res = supabase.auth.sign_up({"email": test_email, "password": test_password})
    print(f"Signup response: {res.user}")
    
    print("Signing in right after signup...")
    login_res = supabase.auth.sign_in_with_password({"email": test_email, "password": test_password})
    print(f"Login response: {login_res}")
except Exception as e:
    print(f"Error occurred: {e}")
