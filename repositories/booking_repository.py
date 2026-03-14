from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository

class BookingRepository(BaseRepository):
    def __init__(self):
        super().__init__("bookings")

    async def find_with_worker(self, booking_id: str) -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name)\
            .select("*, worker:employees(*)")\
            .eq("id", str(booking_id))\
            .execute()
        return result.data[0] if result.data else None

    async def list_by_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name)\
            .select("*, worker:employees(*)")\
            .eq("customer_id", str(customer_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def count_by_customer(self, customer_id: str) -> int:
        client = await self.get_client()
        result = await client.table(self.table_name)\
            .select("id", count="exact")\
            .eq("customer_id", str(customer_id))\
            .execute()
        return result.count or 0

    async def count_all(self) -> int:
        client = await self.get_client()
        result = await client.table(self.table_name).select("id", count="exact").execute()
        return result.count or 0
