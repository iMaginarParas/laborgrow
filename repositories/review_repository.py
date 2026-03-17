from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository

class ReviewRepository(BaseRepository):
    def __init__(self):
        super().__init__("reviews")

    async def list_by_worker(self, worker_id: str) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, customer:employers(*)")\
            .eq("worker_id", str(worker_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def get_average_rating(self, worker_id: str) -> float:
        result = self.get_client().table(self.table_name).select("rating").eq("worker_id", str(worker_id)).execute()
        if not result.data:
            return 0.0
        ratings = [r['rating'] for r in result.data]
        return sum(ratings) / len(ratings)
