from typing import List, Dict, Any, Optional
from repositories.job_repository import JobRepository
from repositories.worker_repository import CategoryRepository
from utils.distance import haversine_distance

class JobService:
    """
    Business logic for job management, optimized for proximity-based
    search and filtering.
    """
    _job_repo = JobRepository()
    _category_repo = CategoryRepository() # Need to import this or manage categories

    @staticmethod
    async def list_jobs(
        city: Optional[str] = None,
        min_salary: Optional[float] = None,
        category_slug: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List active jobs with filters and search keywords.
        """
        category_id = None
        if category_slug:
            # Simple lookup from repository or service
            from services.worker_service import WorkerService
            cats = await WorkerService.list_categories()
            for c in cats:
                if c['slug'] == category_slug:
                    category_id = c['id']
                    break

        jobs = await JobService._job_repo.list_active_jobs(
            city=city,
            min_salary=min_salary,
            category_id=category_id
        )

        if search:
            search = search.lower()
            jobs = [
                j for j in jobs
                if search in (j['title'] or "").lower() or 
                   search in (j['description'] or "").lower()
            ]

        return jobs
    async def get_nearby_jobs(lat: float, lng: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Fetch all jobs, calculate distance to worker,
        and filter within a specified radius (default 10km).
        """
        try:
            # 1. Fetch available jobs using repository
            jobs = await JobService._job_repo.list_all()

            if not jobs:
                return []

            nearby_jobs = []

            # 2. Distance calculation
            for job in jobs:
                job_lat = job.get("lat")
                job_lng = job.get("lng")

                if job_lat is None or job_lng is None:
                    continue

                distance = haversine_distance(lat, lng, job_lat, job_lng)
                
                job_with_distance = dict(job)
                job_with_distance["distance_km"] = round(distance, 2)
                nearby_jobs.append(job_with_distance)

            # 3. Sort by proximity (closest first)
            nearby_jobs.sort(key=lambda x: x["distance_km"])

            return nearby_jobs

        except Exception as e:
            raise e

    @staticmethod
    async def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Unified method to fetch job details.
        """
        return await JobService._job_repo.find_with_category(job_id)

    @staticmethod
    async def create_job(job_in: Dict[str, Any], employer_id: str) -> Dict[str, Any]:
        from services.auth_service import AuthService
        # 1. Ensure employer profile exists (handle role switching)
        profile = await AuthService.get_user_profile(employer_id)
        if profile and profile.get("role") == "employee":
            # User is in employees table, but trying to post a job. 
            # We need them in employers table too.
            employer_data = {
                "id": employer_id,
                "company_name": profile.get("name", "Employer"),
                "phone": profile.get("phone", ""),
                "email": profile.get("email", "")
            }
            # Upsert into employers
            AuthService._user_repo.update_profile(employer_id, "employers", employer_data)

        # 2. Filter out fields that don't belong in the DB or need mapping
        lat = job_in.pop('lat', 0.0)
        lng = job_in.pop('lng', 0.0)
        
        job_data = {
            **job_in,
            "employer_id": employer_id,
            "status": "open",
            "lat_long": f"POINT({lng} {lat})"
        }
        return await JobService._job_repo.insert(job_data)

    @staticmethod
    async def update_job(job_id: str, updates: Dict[str, Any], employer_id: str) -> Optional[Dict[str, Any]]:
        # Ensure ownership
        job = await JobService._job_repo.find_by_id(job_id)
        if not job or str(job.get("employer_id")) != str(employer_id):
            return None
        return await JobService._job_repo.update(job_id, updates)

    @staticmethod
    async def delete_job(job_id: str, employer_id: str) -> bool:
        # Ensure ownership
        job = await JobService._job_repo.find_by_id(job_id)
        if not job or str(job.get("employer_id")) != str(employer_id):
            return False
        return await JobService._job_repo.delete(job_id)

    @staticmethod
    async def list_employer_jobs(employer_id: str) -> List[Dict[str, Any]]:
        return await JobService._job_repo.list_by_employer(employer_id)
