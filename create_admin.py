import asyncio
from core.admin_security import get_password_hash
from database import get_supabase

async def create_super_admin():
    client = get_supabase()
    
    email = "admin@laborgro.in"
    password = "SuperSecretPassword123!"
    
    print(f"Creating Super Admin for: {email}")
    password_hash = get_password_hash(password)
    
    # 1. Create the SUPER_ADMIN role if it doesn't exist
    role_res = client.table("admin_roles").select("id").eq("name", "SUPER_ADMIN").execute()
    
    if not role_res.data:
        print("Creating SUPER_ADMIN role...")
        role_res = client.table("admin_roles").insert({
            "name": "SUPER_ADMIN",
            "permissions": ["all"]
        }).execute()
        
    role_id = role_res.data[0]["id"]
    
    # 2. Check if admin already exists
    admin_res = client.table("admin_users").select("id").eq("email", email).execute()
    if admin_res.data:
        print(f"Updating password for existing admin: {email}")
        client.table("admin_users").update({
            "password_hash": password_hash,
            "is_active": True
        }).eq("email", email).execute()
    else:
        print(f"Creating new admin user: {email}")
        client.table("admin_users").insert({
            "email": email,
            "password_hash": password_hash,
            "role_id": role_id,
            "is_active": True
        }).execute()

    print("\n✅ Admin account ready!")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    asyncio.run(create_super_admin())
