from typing import List, Dict, Any, Optional
import uuid
from repositories.application_repository import ApplicationRepository
from repositories.job_repository import JobRepository
from services.worker_service import WorkerService
from services.notification_service import NotificationService

class ApplicationService:
    _app_repo = ApplicationRepository()
    _job_repo = JobRepository()

    @staticmethod
    async def apply_to_job(job_id: str, worker_id: str) -> Dict[str, Any]:
        """
        Apply to a job. Ensures worker profile exists.
        """
        # Ensure worker profile exists in 'employees' table first
        from services.auth_service import AuthService
        profile = await AuthService.get_user_profile(worker_id)
        if not profile or profile.get("role") != "employee":
             from fastapi import HTTPException
             raise HTTPException(
                 status_code=400, 
                 detail="Please create a worker profile before applying for jobs."
             )

        # Safely convert job_id to integer (jobs table uses integer PKs)
        try:
            job_id_int = int(job_id)
        except (ValueError, TypeError):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job ID format. Expected an integer, got: {job_id}"
            )

        data = {
            "job_id": job_id_int,
            "worker_id": worker_id,
            "status": "pending"
        }
        
        try:
            result = await ApplicationService._app_repo.insert(data)
            
            # Notify Employer
            job = await ApplicationService._job_repo.find_by_id(job_id_int)
            if job and job.get("employer_id"):
                await NotificationService.create_notification(
                    user_id=str(job["employer_id"]),
                    title="New Job Applicant!",
                    message=f"Someone just applied for your job: {job.get('title')}. Review them now.",
                    type="application",
                    link_id=str(job_id_int)
                )
            return result
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="You have already applied for this job.")
            raise e

    @staticmethod
    async def list_job_applicants(job_id: str, employer_id: str) -> List[Dict[str, Any]]:
        # Verify job ownership
        job = await ApplicationService._job_repo.find_by_id(job_id)
        if not job or str(job.get("employer_id")) != str(employer_id):
            return []
        
        apps = await ApplicationService._app_repo.list_by_job(job_id)
        for app in apps:
            if app.get("worker"):
                app["worker"] = WorkerService._format_worker(app["worker"])
        return apps

    @staticmethod
    async def update_application_status(
        application_id: str, 
        status: str, 
        employer_id: str
    ) -> Optional[Dict[str, Any]]:
        # Verify ownership via job
        app = await ApplicationService._app_repo.find_with_details(application_id)
        if not app:
            return None
        
        job = app.get("job")
        if not job or str(job.get("employer_id")) != str(employer_id):
            return None
            
        updated = await ApplicationService._app_repo.update(application_id, {"status": status})
        
        # Notify Worker of update
        if updated:
            job_title = "a job"
            if app.get("job"):
                job_title = f"'{app['job'].get('title')}'"
            
            await NotificationService.create_notification(
                user_id=str(app["worker_id"]),
                title=f"Application {status.capitalize()}!",
                message=f"Your application for {job_title} has been {status}.",
                type="application_status",
                link_id=str(app.get("job_id"))
            )
        return updated

    @staticmethod
    async def list_worker_applications(worker_id: str) -> List[Dict[str, Any]]:
        return await ApplicationService._app_repo.list_by_worker(worker_id)

    @staticmethod
    async def withdraw_application(application_id: str, worker_id: str) -> bool:
        # Verify ownership
        app = await ApplicationService._app_repo.find_by_id(application_id)
        if not app or str(app.get("worker_id")) != str(worker_id):
            return False
        return await ApplicationService._app_repo.delete(application_id)
