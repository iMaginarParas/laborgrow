from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from database import supabase
from utils.distance import haversine_distance

class JobService:
    """
    Business logic for job management, optimized for proximity-based
    search and filtering.
    """

    @staticmethod
    async def get_nearby_jobs(lat: float, lng: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from Supabase, calculate distance to worker,
        and filter within a specified radius (default 10km).
        """
        try:
            # 1. Fetch available jobs from Supabase
            response = supabase.table("jobs").select("*").execute()
            jobs = response.data

            if not jobs:
                return []

            nearby_jobs = []

            # 2. Parallel processing of distance (Sequential here for MVP clarity)
            for job in jobs:
                job_lat = job.get("lat")
                job_lng = job.get("lng")

                if job_lat is None or job_lng is None:
                    continue

                # Use the relocated distance utility
                distance = haversine_distance(lat, lng, job_lat, job_lng)

                if distance <= radius_km:
                    job_with_distance = dict(job)
                    job_with_distance["distance_km"] = round(distance, 2)
                    nearby_jobs.append(job_with_distance)

            # 3. Sort by proximity (closest first)
            nearby_jobs.sort(key=lambda x: x["distance_km"])

            return nearby_jobs

        except Exception as e:
            # Let global handler pick up unexpected errors for polite reporting
            raise e

    @staticmethod
    async def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Unified method to fetch job details.
        """
        try:
            response = supabase.table("jobs").select("*").eq("id", job_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise e
