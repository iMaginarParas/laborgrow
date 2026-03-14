from typing import Dict, Any, Optional
from database import get_supabase

class UserRepository:
    """
    Handles user profile lookups across employees and employers tables.
    """
    def find_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
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

    def update_profile(self, user_id: str, table_name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        client = get_supabase()
        result = client.table(table_name).update(updates).eq("id", user_id).execute()
        return result.data[0] if result.data else None
