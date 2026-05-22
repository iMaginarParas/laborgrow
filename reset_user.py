import asyncio
from database import get_supabase

async def reset_password():
    client = get_supabase()
    email = "darshanurs54@gmail.com"
    new_password = "Password123!"
    
    print(f"Looking for user {email}...")
    
    # We have to find the user in auth.users. But Supabase python client admin api
    # has a list_users method.
    users = client.auth.admin.list_users()
    target_user = None
    for u in users:
        if u.email == email:
            target_user = u
            break
            
    if target_user:
        print(f"Found user {target_user.id}. Resetting password...")
        client.auth.admin.update_user_by_id(target_user.id, {"password": new_password})
        print(f"Password reset to: {new_password}")
    else:
        print("User not found!")

asyncio.run(reset_password())
