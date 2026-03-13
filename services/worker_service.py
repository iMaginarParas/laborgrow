from typing import List, Optional, Dict, Any
import uuid

from database import supabase

class WorkerService:
    """
    Coordinator for the supply-side of the marketplace (Workers/Categories) using Supabase.
    """

    @staticmethod
    def _format_worker(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats flat row from 'employees' table into the nested structure 
        expected by the Flutter app.
        """
        work_details = data.get("work_details") or {}
        return {
            "id": data.get("id"),
            "bio": work_details.get("bio", data.get("bio") or ""),
            "city": data.get("city") or "",
            "lat": data.get("lat") or 0.0,
            "lng": data.get("lng") or 0.0,
            "experience_years": work_details.get("experience_years", data.get("experience_years") or 0),
            "hourly_rate": work_details.get("hourly_rate", data.get("hourly_rate") or 500.0),
            "rating": data.get("rating") or 4.5,
            "is_verified": data.get("is_verified") or False,
            "is_available": data.get("is_available") if data.get("is_available") is not None else True,
            "user": {
                "id": data.get("id"),
                "name": data.get("full_name") or "Worker",
                "email": data.get("email") or "",
                "phone": data.get("phone") or "",
                "profile_pic_url": data.get("profile_pic_url"),
                "created_at": data.get("created_at")
            },
            # Fallback lists to prevent parsing errors
            "categories": data.get("categories") or [
                {"id": 1, "name": "General", "emoji": "🛠️", "slug": "general"}
            ],
            "skills": [{"skill_name": s} for s in (data.get("skills") or [])] if isinstance(data.get("skills"), list) else []
        }

    @staticmethod
    async def list_workers(
        category_slug: Optional[str] = None,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query the employees pool via Supabase.
        """
        query = supabase.table("employees").select("*")
        
        if min_rating:
            query = query.gte("rating", min_rating)
        
        if max_price:
            query = query.lte("hourly_rate", max_price)

        result = query.execute()
        workers = result.data or []
            
        return [WorkerService._format_worker(w) for w in workers]

    @staticmethod
    async def get_worker_detail(
        worker_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch employee with profile metadata.
        """
        result = supabase.table("employees")\
            .select("*")\
            .eq("id", str(worker_id))\
            .execute()
        
        if result.data:
            return WorkerService._format_worker(result.data[0])
        return None

    @staticmethod
    async def list_categories() -> List[Dict[str, Any]]:
        """
        Retrieve all marketplace service categories (Returns empty list if missing).
        """
        try:
            result = supabase.table("categories").select("*").execute()
            return result.data or []
        except:
             return []

