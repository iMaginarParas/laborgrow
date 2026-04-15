
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

load_dotenv()

from database import init_supabase, get_supabase
from services.admin_service import AdminService
from sqlalchemy.orm import Session
from database_sqlalchemy import SessionLocal

def test_users():
    print("Initializing Supabase...")
    init_supabase()
    
    print("Fetching users via AdminService...")
    db = SessionLocal()
    try:
        result = AdminService.get_paginated_users(db, skip=0, limit=2)
        print("SUCCESS!")
        print(f"Total: {result['total']}")
        print(f"Data: {result['data']}")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_users()
