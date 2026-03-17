from typing import Dict, Any, List
from repositories.application_repository import ApplicationRepository
from repositories.worker_repository import WorkerRepository
from services.review_service import ReviewService
from services.worker_service import WorkerService

class WorkerDashboardService:
    _app_repo = ApplicationRepository()
    _worker_repo = WorkerRepository()

    @staticmethod
    async def get_dashboard_data(worker_id: str) -> Dict[str, Any]:
        # Fetch applications
        apps = await WorkerDashboardService._app_repo.list_by_worker(worker_id)
        
        pending_apps = [a for a in apps if a.get("status") == "pending"]
        accepted_apps = [a for a in apps if a.get("status") == "accepted"]
        rejected_apps = [a for a in apps if a.get("status") == "rejected"]
        
        # Fetch worker profile info
        worker = await WorkerDashboardService._worker_repo.find_by_id(worker_id)
        profile_stats = {
            "is_available": worker.get("is_available", True) if worker else True,
            "rating": worker.get("rating", 0.0) if worker else 0.0,
            "is_verified": worker.get("is_verified", False) if worker else False
        }
        
        # Fetch rating stats
        rating_stats = await ReviewService.get_worker_rating_stats(worker_id)
        
        return {
            "applications": {
                "total": len(apps),
                "pending": len(pending_apps),
                "accepted": len(accepted_apps),
                "rejected": len(rejected_apps),
                "recent": apps[:5]
            },
            "profile": profile_stats,
            "ratings": rating_stats
        }
