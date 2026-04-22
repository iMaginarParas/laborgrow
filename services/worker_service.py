from typing import List, Optional, Dict, Any
import uuid
import json

from repositories.worker_repository import WorkerRepository, CategoryRepository

class WorkerService:
    """
    Coordinator for the supply-side of the marketplace (Workers/Categories).
    De-coupled from direct DB access via Repositories.
    """
    _worker_repo = WorkerRepository()
    _category_repo = CategoryRepository()

    @staticmethod
    def _format_worker(data: Dict[str, Any], categories_map: Dict[int, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Formats flat row from 'employees' table into the nested structure 
        expected by the Flutter app.
        """
        raw_work_details = data.get("work_details") or {}
        # Supabase may return JSONB columns as a raw string in some envs — parse if needed
        if isinstance(raw_work_details, str):
            try:
                work_details = json.loads(raw_work_details)
            except (json.JSONDecodeError, ValueError):
                work_details = {}
        elif isinstance(raw_work_details, dict):
            work_details = raw_work_details
        else:
            work_details = {}
        
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
            "daily_rate": work_details.get("daily_rate", work_details.get("hourly_rate", data.get("hourly_rate") or 500.0)),
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
        city: Optional[str] = None,
        is_available: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the employees pool with business logic filtering.
        """
        # Fetch categories for mapping
        all_cats = await WorkerService.list_categories()
        categories_map = {c['id']: c for c in all_cats}
        
        workers = await WorkerService._worker_repo.list_active_workers(
            min_rating=min_rating,
            city=city,
            is_available=is_available
        )
        
        formatted_workers = [WorkerService._format_worker(w, categories_map) for w in workers]
        
        # Filter by category slug in Python for now to support work_details JSON mapping
        if category_slug:
            formatted_workers = [
                w for w in formatted_workers 
                if any(cat['slug'] == category_slug for cat in w['categories'])
            ]
            
        # Filter by price in Python if daily_rate is in work_details
        if max_price:
            formatted_workers = [
                w for w in formatted_workers
                if w['daily_rate'] <= max_price
            ]
            
        # Filter by search keyword (name or skills)
        if search:
            search = search.lower()
            formatted_workers = [
                w for w in formatted_workers
                if search in (w['user']['name'] or "").lower() or 
                   any(search in s['skill_name'].lower() for s in w['skills']) or
                   any(search in c['name'].lower() for c in w['categories'])
            ]
            
        return formatted_workers

    @staticmethod
    async def get_worker_detail(
        worker_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch employee with profile metadata formatted for the frontend.
        """
        # Fetch categories for mapping
        all_cats = await WorkerService.list_categories()
        categories_map = {c['id']: c for c in all_cats}

        data = await WorkerService._worker_repo.find_by_id(worker_id)
        
        if data:
            return WorkerService._format_worker(data, categories_map)
        return None

    @staticmethod
    async def list_categories() -> List[Dict[str, Any]]:
        """
        Retrieve all marketplace service categories.
        """
        try:
            return await WorkerService._category_repo.list_all()
        except Exception:
             return []

