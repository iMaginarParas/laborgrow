from typing import List, Dict, Any, Optional
from repositories.job_repository import JobRepository
from utils.distance import haversine_distance

class JobService:
    """
    Business logic for job management, optimized for proximity-based
    search and filtering.
    """
    _job_repo = JobRepository()

    @staticmethod
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

                if distance <= radius_km:
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
        return await JobService._job_repo.find_by_id(job_id)
