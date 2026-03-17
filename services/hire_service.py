from typing import List, Dict, Any, Optional
from repositories.job_repository import JobRepository
from repositories.worker_repository import WorkerRepository
from repositories.application_repository import ApplicationRepository
from services.worker_service import WorkerService

class HireService:
    _job_repo = JobRepository()
    _worker_repo = WorkerRepository()
    _app_repo = ApplicationRepository()

    @staticmethod
    async def get_dashboard_stats(employer_id: str) -> Dict[str, Any]:
        jobs = await HireService._job_repo.list_by_employer(employer_id)
        job_ids = [str(j['id']) for j in jobs]
        
        # Count total applicants across all jobs
        total_applicants = 0
        for jid in job_ids:
            apps = await HireService._app_repo.list_by_job(jid)
            total_applicants += len(apps)
            
        return {
            "total_jobs": len(jobs),
            "total_applicants": total_applicants,
            "recent_jobs": jobs[:5]
        }

    @staticmethod
    async def get_worker_matches(employer_id: str) -> List[Dict[str, Any]]:
        """
        Match workers based on categories of open jobs by this employer.
        """
        jobs = await HireService._job_repo.list_by_employer(employer_id)
        if not jobs:
            return await WorkerService.list_workers() # Return general top workers if no jobs
            
        category_ids = list(set([j.get("category_id") for j in jobs if j.get("category_id")]))
        # For simplicity, we just fetch workers in these categories
        all_workers = await WorkerService.list_workers()
        matches = []
        for w in all_workers:
            w_cat_ids = [c['id'] for c in w.get('categories', [])]
            if any(cid in w_cat_ids for cid in category_ids):
                matches.append(w)
                
        return matches[:10]
