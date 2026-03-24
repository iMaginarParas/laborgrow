from typing import Dict, Any, Optional
from database import get_supabase

class UserRepository:
    """
    Handles user profile lookups across employees and employers tables.
    """
    async def find_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        client = get_supabase()

        # Try employees first, but only if they have basic info (email)
        res = client.table("employees").select("*").eq("id", user_id).execute()
        if res.data and res.data[0].get("email") is not None:
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
        
        # Strip 'phone' from employer updates (column doesn't exist in employers table)
        if table_name == "employers":
            updates.pop("phone", None)
        
        # Fetch existing row and merge to preserve non-null required columns
        existing_res = client.table(table_name).select("*").eq("id", user_id).execute()
        if existing_res.data:
            existing = dict(existing_res.data[0])
            # Merge: existing values are overridden by updates, preserving untouched fields
            merged = {**existing, **updates}
        else:
            # New row — use updates as-is but ensure id is present
            merged = dict(updates)
        
        merged["id"] = user_id  # Always ensure id is present for upsert
        
        result = client.table(table_name).upsert(merged).execute()
        return result.data[0] if result.data else None
