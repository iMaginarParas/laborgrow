import os
import asyncio
from dotenv import load_dotenv
from database import get_supabase
from core.admin_security import get_password_hash

async def seed_admin():
    load_dotenv()
    client = get_supabase()
    
    email = "admin@laborgro.in"
    password = "admin" # A default password for testing, the user can change it later
    hashed_password = get_password_hash(password)
    
    # 1. Ensure the admin_roles table has a super_admin role
    roles_res = client.table("admin_roles").select("*").eq("name", "super_admin").execute()
    role_id = None
    if not roles_res.data:
        print("Inserting super_admin role...")
        insert_res = client.table("admin_roles").insert({
            "name": "super_admin"
        }).execute()
        role_id = insert_res.data[0]["id"]
    else:
        role_id = roles_res.data[0]["id"]
        
    print(f"Role ID: {role_id}")
    
    # 2. Check if admin user exists
    user_res = client.table("admin_users").select("*").eq("email", email).execute()
    if not user_res.data:
        print(f"Inserting admin user {email}...")
        admin_res = client.table("admin_users").insert({
            "email": email,
            "password_hash": hashed_password,
            "role_id": role_id,
            "is_active": True
        }).execute()
        print(f"Inserted: {admin_res.data}")
    else:
        print(f"Admin user {email} already exists! Updating password...")
        admin_res = client.table("admin_users").update({
            "password_hash": hashed_password,
            "role_id": role_id
        }).eq("email", email).execute()
        print(f"Updated: {admin_res.data}")

if __name__ == "__main__":
    asyncio.run(seed_admin())
