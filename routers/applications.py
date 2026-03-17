from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from dependencies.auth import get_current_user
from services.application_service import ApplicationService
from models.schemas import ApplicationCreate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Job Applications"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    app_in: ApplicationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Worker applies to a job.
    """
    return await ApplicationService.apply_to_job(str(app_in.job_id), current_user["id"])

@router.get("/job/{job_id}", response_model=List[ApplicationResponse])
async def list_job_applicants(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Employer lists applicants for their job.
    """
    return await ApplicationService.list_job_applicants(job_id, current_user["id"])

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_update: Dict[str, str], # {"status": "accepted"/"rejected"}
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Employer accepts or rejects an applicant.
    """
    new_status = status_update.get("status")
    if new_status not in ["accepted", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    app = await ApplicationService.update_application_status(application_id, new_status, current_user["id"])
    if not app:
        raise HTTPException(status_code=403, detail="Not authorized or application not found")
    return app

@router.get("/my-applications", response_model=List[ApplicationResponse])
async def list_my_applications(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Worker lists their own applications.
    """
    return await ApplicationService.list_worker_applications(current_user["id"])

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_application(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Worker withdraws their application.
    """
    success = await ApplicationService.withdraw_application(application_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=403, detail="Not authorized or application not found")
    return
