from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository

class JobRepository(BaseRepository):
    def __init__(self):
        super().__init__("jobs")

    async def count_all(self) -> int:
        result = self.get_client().table(self.table_name).select("id", count="exact").execute()
        return result.count or 0

    async def list_all(self, select: str = "*, category:categories(*)") -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name).select(select).execute()
        return result.data or []

    async def list_active_jobs(
        self,
        city: Optional[str] = None,
        min_salary: Optional[float] = None,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = self.get_client().table(self.table_name).select("*, category:categories(*)")\
            .eq("status", "open")
        
        if city:
            query = query.ilike("job_city", f"%{city}%")
        if min_salary:
            query = query.gte("salary_min", min_salary)
        if category_id:
            query = query.eq("category_id", category_id)
            
        result = query.order("created_at", desc=True).execute()
        return result.data or []

    async def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("id, title, job_city, created_at")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data or []

    async def list_by_employer(self, employer_id: str) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, category:categories(*)")\
            .eq("employer_id", str(employer_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def find_with_category(self, job_id: str) -> Optional[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, category:categories(*)")\
            .eq("id", str(job_id))\
            .execute()
        return result.data[0] if result.data else None
