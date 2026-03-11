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
        return {
            "id": data.get("id"),
            "bio": data.get("bio", ""),
            "city": data.get("city", ""),
            "lat": data.get("lat", 0.0),
            "lng": data.get("lng", 0.0),
            "experience_years": data.get("experience_years", 0),
            "hourly_rate": data.get("hourly_rate", 500.0),
            "rating": data.get("rating", 4.5),
            "is_verified": data.get("is_verified", False),
            "is_available": data.get("is_available", True),
            "user": {
                "id": data.get("id"),
                "name": data.get("full_name", "Worker"),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "profile_pic_url": data.get("profile_pic_url"),
                "created_at": data.get("created_at")  # Pydantic will handle None if optional
            },
            # Fallback lists to prevent parsing errors
            "categories": data.get("categories") or [
                {"id": 1, "name": "General", "emoji": "🛠️", "slug": "general"}
            ],
            "skills": data.get("skills") or []
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

