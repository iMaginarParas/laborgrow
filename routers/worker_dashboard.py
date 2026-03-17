from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from dependencies.auth import get_current_user
from services.worker_dashboard_service import WorkerDashboardService
from services.auth_service import AuthService

router = APIRouter(prefix="/worker", tags=["Worker Dashboard"])

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_worker_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Overview of applications, ratings and profile status for the worker.
    """
    return await WorkerDashboardService.get_dashboard_data(current_user["id"])

@router.get("/profile", response_model=Dict[str, Any])
async def get_my_worker_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Fetch full worker profile details for the logged-in user.
    """
    from services.worker_service import WorkerService
    profile = await WorkerService.get_worker_detail(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")
    return profile

@router.post("/availability")
async def toggle_availability(
    status: Dict[str, bool], # {"available": true/false}
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Toggle worker availability status.
    """
    available = status.get("available")
    if available is None:
        raise HTTPException(status_code=400, detail="Missing 'available' field")
        
    profile = await AuthService.update_user_profile(current_user["id"], {"is_available": available})
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")
        
    return {"status": "success", "is_available": available}
