from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository

class WorkerRepository(BaseRepository):
    def __init__(self):
        super().__init__("employees")

    async def count_all(self) -> int:
        result = self.get_client().table(self.table_name).select("id", count="exact").execute()
        return result.count or 0

    async def list_active_workers(self, min_rating: float = 0.0) -> List[Dict[str, Any]]:
        query = self.get_client().table(self.table_name).select("*")
        if min_rating > 0:
            query = query.gte("rating", min_rating)
        result = query.execute()
        return result.data or []

class CategoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("categories")
