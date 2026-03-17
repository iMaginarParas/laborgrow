from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from dependencies.auth import get_current_user
from services.hire_service import HireService

router = APIRouter(prefix="/hire", tags=["Hire (Employer) Dashboard"])

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_hire_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Overview of jobs and applications for the employer.
    """
    return await HireService.get_dashboard_stats(current_user["id"])

@router.get("/matches", response_model=List[Dict[str, Any]])
async def get_worker_matches(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get recommended workers based on employer's posted jobs.
    """
    return await HireService.get_worker_matches(current_user["id"])
