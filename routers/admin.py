from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

from database import supabase
from config.settings import settings

router = APIRouter(prefix="/admin", tags=["Administrator Operations"])

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
    Marketplace overview — statistics and recent activity from Supabase.
    """
    try:
        total_jobs         = supabase.table("jobs").select("id", count="exact").execute()
        total_bookings     = supabase.table("bookings").select("id", count="exact").execute()
        # Use employees table as it's the primary user entity in our schema
        total_users        = supabase.table("employees").select("id", count="exact").execute()

        recent_jobs = (
            supabase.table("jobs")
            .select("id, title, job_city, created_at") # Company name might be missing in simple schema
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        return {
            "status": "success",
            "stats": {
                "total_jobs":         total_jobs.count or 0,
                "total_bookings":     total_bookings.count or 0,
                "total_users":        total_users.count or 0,
            },
            "recent_jobs": recent_jobs.data or [],
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
        res = supabase.table("employees").update({"is_verified": True}).eq("id", worker_id).execute()
        if not res.data:
             raise HTTPException(status_code=404, detail="Worker record not found.")
        return {"message": "Worker successfully approved."}
    except Exception as e:
        raise e
