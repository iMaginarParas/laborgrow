from typing import List, Dict, Any, Optional, TypeVar, Generic
from supabase import AsyncClient
from database import get_supabase

T = TypeVar("T")

class BaseRepository:
    """
    Standard asynchronous data access patterns for Supabase.
    """
    def __init__(self, table_name: str):
        self.table_name = table_name

    async def get_client(self) -> AsyncClient:
        return await get_supabase()

    async def list_all(self, select: str = "*") -> List[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name).select(select).execute()
        return result.data or []

    async def find_by_id(self, id_val: Any, select: str = "*") -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name).select(select).eq("id", str(id_val)).execute()
        return result.data[0] if result.data else None

    async def insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        client = await self.get_client()
        result = await client.table(self.table_name).insert(data).execute()
        return result.data[0] if result.data else data

    async def update(self, id_val: Any, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name).update(updates).eq("id", str(id_val)).execute()
        return result.data[0] if result.data else None

    async def delete(self, id_val: Any) -> bool:
        client = await self.get_client()
        await client.table(self.table_name).delete().eq("id", str(id_val)).execute()
        return True
