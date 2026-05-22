import asyncio
from database import get_supabase
from core.admin_security import verify_password
from dotenv import load_dotenv

async def test_auth():
    load_dotenv()
    client = get_supabase()
    
    search_email = "admin@laborgro.in".lower().strip()
    
    res = client.table("admin_users") \
        .select("*, admin_roles(name)") \
        .eq("email", search_email) \
        .execute()
        
    if not res.data:
        print(f"Admin user not found: {search_email}")
        return
        
    admin = res.data[0]
    print(f"Found admin: {admin}")
    
    # Check password
    if not verify_password("admin", admin["password_hash"]):
        print("Password verification failed")
    else:
        print("Login SUCCESS!")

if __name__ == "__main__":
    asyncio.run(test_auth())
