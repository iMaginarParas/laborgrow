from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_sqlalchemy import get_db
from dependencies.admin_auth import role_required
from services.admin_service import AdminService
from typing import Dict, Any

router = APIRouter(prefix="/admin", tags=["Admin Control Center"])

@router.get("/dashboard/summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    """
    Unified dashboard for operational metrics and system status.
    """
    try:
        # Fetch real metrics from the database
        metrics = AdminService.get_dashboard_metrics(db)
        
        system_health = {
            "api": "healthy",
            "database": "connected",
            "background_workers": "active"
        }
        
        return {
            "metrics": metrics,
            "system_health": system_health,
            "active_incidents": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
