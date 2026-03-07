from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs Marketplace"])

@router.get("/nearby", response_model=List[Dict[str, Any]])
async def get_nearby_jobs(
    lat: float = Query(..., description="Latitude of your current location"),
    lng: float = Query(..., description="Longitude of your current location"),
    radius_km: float = Query(10.0, description="Search distance in kilometers")
) -> List[Dict[str, Any]]:
    """
    Search for jobs within 10 km (or custom radius) of your current location.
    Optimized for LaborGrow marketplace performance.
    """
    try:
        # Business logic isolated in JobService
        return await JobService.get_nearby_jobs(lat, lng, radius_km)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_detail(job_id: str) -> Dict[str, Any]:
    """
    Retrieve full details for a specific job entry.
    """
    job = await JobService.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job entry not found")
    return job
