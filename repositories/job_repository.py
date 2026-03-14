from repositories.base_repository import BaseRepository

class JobRepository(BaseRepository):
    def __init__(self):
        super().__init__("jobs")

    async def count_all(self) -> int:
        client = await self.get_client()
        result = await client.table(self.table_name).select("id", count="exact").execute()
        return result.count or 0

    async def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        client = await self.get_client()
        result = await client.table(self.table_name)\
            .select("id, title, job_city, created_at")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data or []
