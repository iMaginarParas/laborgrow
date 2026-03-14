from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository
from database import get_supabase

class UserRepository:
    """
    Handles user profile lookups across employees and employers tables.
    """
    async def find_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        client = await get_supabase()
        
        # Try employees first
        res = await client.table("employees").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["role"] = "employee"
            return profile
        
        # Try employers
        res = await client.table("employers").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["role"] = "employer"
            return profile
            
        return None

    async def update_profile(self, user_id: str, table_name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        client = await get_supabase()
        result = await client.table(table_name).update(updates).eq("id", user_id).execute()
        return result.data[0] if result.data else None
