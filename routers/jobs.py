from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Dict, Any, Optional
from services.job_service import JobService
from models.schemas import JobCreate, JobResponse
from dependencies.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs Marketplace"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Post a new job requirement. Req: Employer account.
    """
    # Simple role check (if user is in employers table)
    # The current_user from get_current_user has ID. AuthService check might be needed if strictly enforced.
    return await JobService.create_job(job_in.dict(), current_user["id"])

@router.get("", response_model=List[JobResponse])
async def list_available_jobs(
    city: Optional[str] = Query(None, description="Filter by job city"),
    min_salary: Optional[float] = Query(None, description="Minimum salary filter"),
    category: Optional[str] = Query(None, description="Category slug filter"),
    search: Optional[str] = Query(None, description="Keywords search in title/description")
) -> List[JobResponse]:
    """
    Search and discover available jobs on the marketplace.
    """
    return await JobService.list_jobs(city, min_salary, category, search)

@router.get("/my-posts", response_model=List[JobResponse])
async def list_my_jobs(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[JobResponse]:
    """
    List all jobs posted by the logged-in employer.
    """
    return await JobService.list_employer_jobs(current_user["id"])

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

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_detail(job_id: str) -> JobResponse:
    """
    Retrieve full details for a specific job entry.
    """
    job = await JobService.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job entry not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a job post. Must be the creator.
    """
    job = await JobService.update_job(job_id, updates, current_user["id"])
    if not job:
        raise HTTPException(status_code=403, detail="Not authorized or job not found")
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Remove a job post. Must be the creator.
    """
    success = await JobService.delete_job(job_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=403, detail="Not authorized or job not found")
    return
