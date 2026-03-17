from typing import Dict, Any, Optional
from database import get_supabase

class UserRepository:
    """
    Handles user profile lookups across employees and employers tables.
    """
    async def find_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        client = get_supabase()

        # Try employees first
        res = client.table("employees").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["role"] = "employee"
            return profile

        # Try employers
        res = client.table("employers").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["role"] = "employer"
            return profile

        return None

    async def update_profile(self, user_id: str, table_name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        client = get_supabase()
        
        # Security: Strip 'phone' from employer updates (column doesn't exist)
        if table_name == "employers":
            updates.pop("phone", None)
            
        # Use upsert to handle cases where the profile doesn't exist yet
        updates["id"] = user_id # Ensure ID is present for upsert
        result = client.table(table_name).upsert(updates).execute()
        return result.data[0] if result.data else None
