from typing import List, Optional, Dict, Any
import uuid

from database import supabase

class WorkerService:
    """
    Coordinator for the supply-side of the marketplace (Workers/Categories) using Supabase.
    """

    @staticmethod
    def _format_worker(data: Dict[str, Any], categories_map: Dict[int, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Formats flat row from 'employees' table into the nested structure 
        expected by the Flutter app.
        """
        work_details = data.get("work_details") or {}
        
        # Resolve categories from IDs in work_details
        categories = []
        if categories_map and "category_ids" in work_details:
            cat_ids = work_details.get("category_ids", [])
            if isinstance(cat_ids, list):
                for cid in cat_ids:
                    if cid in categories_map:
                        categories.append(categories_map[cid])
        
        # Fallback to default if no categories found
        if not categories:
            categories = data.get("categories") or [
                {"id": 1, "name": "General", "emoji": "🛠️", "slug": "general"}
            ]

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
            "categories": categories,
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
        # Fetch categories for mapping
        all_cats = await WorkerService.list_categories()
        categories_map = {c['id']: c for c in all_cats}
        
        query = supabase.table("employees").select("*")
        
        if min_rating:
            query = query.gte("rating", min_rating)
        
        # max_price filter might need adjustments if hourly_rate is in work_details
        # For now, we query all and filter complex things in Python if needed
        # but simple top-level columns are better
            
        result = query.execute()
        workers = result.data or []
        
        formatted_workers = [WorkerService._format_worker(w, categories_map) for w in workers]
        
        # Filter by category slug in Python for now to support work_details JSON mapping
        if category_slug:
            formatted_workers = [
                w for w in formatted_workers 
                if any(cat['slug'] == category_slug for cat in w['categories'])
            ]
            
        # Filter by price in Python if hourly_rate is in work_details
        if max_price:
            formatted_workers = [
                w for w in formatted_workers
                if w['hourly_rate'] <= max_price
            ]
            
        return formatted_workers

    @staticmethod
    async def get_worker_detail(
        worker_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch employee with profile metadata.
        """
        # Fetch categories for mapping
        all_cats = await WorkerService.list_categories()
        categories_map = {c['id']: c for c in all_cats}

        result = supabase.table("employees")\
            .select("*")\
            .eq("id", str(worker_id))\
            .execute()
        
        if result.data:
            return WorkerService._format_worker(result.data[0], categories_map)
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

