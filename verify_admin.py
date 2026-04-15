import asyncio
from core.admin_security import verify_password
from database import get_supabase

async def check_admin():
    client = get_supabase()
    email = "admin@laborgro.in"
    password = "SuperSecretPassword123!"
    
    print("Fetching admin user from database...")
    res = client.table("admin_users").select("*").eq("email", email).execute()
    
    if not res.data:
        print("ERROR: User not found in database!")
        return

    admin = res.data[0]
    print(f"User found: {admin['email']}")
    print(f"Role ID: {admin.get('role_id')}")
    print(f"Is Active: {admin.get('is_active')}")
    
    print(f"\nChecking password hash...")
    password_hash = admin["password_hash"]
    
    is_valid = verify_password(password, password_hash)
    if is_valid:
        print("Password verified successfully against hash.")
    else:
        print("ERROR: Password did NOT match hash!")
        
    print("\nChecking role fetch as done in router...")
    role_res = client.table("admin_users").select("*, admin_roles(name)").eq("email", email).execute()
    if role_res.data:
        role_data = role_res.data[0]
        if "admin_roles" in role_data and role_data["admin_roles"]:
            print(f"Role fetched successfully: {role_data['admin_roles'].get('name')}")
        else:
            print("ERROR: Could not fetch role! 'admin_roles' might be missing, or the foreign key isn't setup correctly.")
            print("Returned data:", role_data)
    else:
        print("ERROR: Second query failed unexpectedly.")

if __name__ == "__main__":
    asyncio.run(check_admin())
