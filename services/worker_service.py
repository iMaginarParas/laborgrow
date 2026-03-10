from typing import List, Optional, Dict, Any
import uuid

from database import supabase

class WorkerService:
    """
    Coordinator for the supply-side of the marketplace (Workers/Categories) using Supabase.
    """

    @staticmethod
    async def list_workers(
        category_slug: Optional[str] = None,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query the worker pool with multi-criteria filtering via Supabase.
        """
        # Start query with joins
        query = supabase.table("workers").select("*, user:users(*), categories:categories(*), skills:worker_skills(*)")
        
        query = query.eq("is_active", is_active)

        if min_rating:
            query = query.gte("rating", min_rating)
        
        if max_price:
            query = query.lte("hourly_rate", max_price)

        # Filtering by category slug requires a separate join or post-filtering
        # In Supabase SDK, we can filter on nested components if the relationship is configured
        if category_slug:
            # We filter by the slug in the categories join
            query = query.eq("categories.slug", category_slug)

        result = query.execute()
        
        # If we filtered by category slug, Supabase SDK might return workers with empty 'categories' list
        # We should filter them out in Python for correctness if the SDK doesn't do it automatically
        workers = result.data or []
        if category_slug:
            workers = [w for w in workers if w.get("categories") and any(c["slug"] == category_slug for c in w["categories"])]
            
        return workers

    @staticmethod
    async def get_worker_detail(
        worker_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch worker with full profile and skills metadata.
        """
        result = supabase.table("workers")\
            .select("*, user:users(*), categories:categories(*), skills:worker_skills(*)")\
            .eq("id", str(worker_id))\
            .execute()
        
        return result.data[0] if result.data else None

    @staticmethod
    async def list_categories() -> List[Dict[str, Any]]:
        """
        Retrieve all marketplace service categories.
        """
        result = supabase.table("categories").select("*").execute()
        return result.data or []

