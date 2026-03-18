from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository

class ApplicationRepository(BaseRepository):
    def __init__(self):
        super().__init__("applications")

    async def list_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, worker:employees(*)")\
            .eq("job_id", str(job_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def list_by_worker(self, worker_id: str) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, job:jobs(*)")\
            .eq("worker_id", str(worker_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def find_with_details(self, application_id: str) -> Optional[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*, job:jobs(*, employer:employers(*)), worker:employees(*)")\
            .eq("id", str(application_id))\
            .execute()
        return result.data[0] if result.data else None
