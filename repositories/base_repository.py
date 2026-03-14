from typing import List, Dict, Any, Optional
from supabase import Client
from database import get_supabase

class BaseRepository:
    """
    Standard synchronous data access patterns for Supabase.
    """
    def __init__(self, table_name: str):
        self.table_name = table_name

    def get_client(self) -> Client:
        return get_supabase()

    async def list_all(self, select: str = "*") -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name).select(select).execute()
        return result.data or []

    async def find_by_id(self, id_val: Any, select: str = "*") -> Optional[Dict[str, Any]]:
        result = self.get_client().table(self.table_name).select(select).eq("id", str(id_val)).execute()
        return result.data[0] if result.data else None

    async def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.get_client().table(self.table_name).insert(data).execute()
        return result.data[0] if result.data else data

    async def update(self, id_val: Any, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = self.get_client().table(self.table_name).update(updates).eq("id", str(id_val)).execute()
        return result.data[0] if result.data else None

    async def delete(self, id_val: Any) -> bool:
        self.get_client().table(self.table_name).delete().eq("id", str(id_val)).execute()
        return True
