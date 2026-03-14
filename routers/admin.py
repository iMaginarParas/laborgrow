from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

from config.settings import settings
from repositories.worker_repository import WorkerRepository
from repositories.job_repository import JobRepository
from repositories.booking_repository import BookingRepository

router = APIRouter(prefix="/admin", tags=["Administrator Operations"])

# Repositories
_worker_repo = WorkerRepository()
_job_repo = JobRepository()
_booking_repo = BookingRepository()

# ── Auth Dependency ────────────────────────────────────────────────────────────

def require_admin(x_admin_key: str = Header(...)):
    """Validates X-Admin-Key header against ADMIN_SECRET_KEY in settings."""
    admin_key = settings.ADMIN_SECRET_KEY or "change-me-in-env"
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key.")

# ── Models ────────────────────────────────────────────────────────────────────

class AdminJobUpdate(BaseModel):
    title:            Optional[str]   = None
    openings:         Optional[int]   = None
    job_city:         Optional[str]   = None
    salary_min:       Optional[float] = None
    salary_max:       Optional[float] = None

# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", dependencies=[Depends(require_admin)])
async def admin_dashboard():
    """
    Marketplace overview — statistics and recent activity.
    """
    try:
        total_jobs = await _job_repo.count_all()
        total_bookings = await _booking_repo.count_all()
        total_users = await _worker_repo.count_all()

        recent_jobs = await _job_repo.list_recent(limit=5)

        return {
            "status": "success",
            "stats": {
                "total_jobs":         total_jobs,
                "total_bookings":     total_bookings,
                "total_users":        total_users,
            },
            "recent_jobs": recent_jobs,
        }
    except Exception as e:
        raise e

@router.post("/workers/{worker_id}/approve", response_model=Dict[str, str], dependencies=[Depends(require_admin)])
async def approve_worker(
    worker_id: str
) -> Dict[str, str]:
    """
    Approve a newly registered worker for inclusion in the marketplace.
    """
    try:
        res = await _worker_repo.update(worker_id, {"is_verified": True})
        if not res:
             raise HTTPException(status_code=404, detail="Worker record not found.")
        return {"message": "Worker successfully approved."}
    except Exception as e:
        raise e
