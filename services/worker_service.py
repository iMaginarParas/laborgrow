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
        Query the employees pool via Supabase.
        """
        # Start query on employees
        query = supabase.table("employees").select("*")
        
        # Filtering (only use available columns)
        # Note: If is_active/rating/hourly_rate aren't in the schema, we skip filtering on them for now
        # result = query.execute()
        
        # Based on inspection, we have: ['id', 'email', 'full_name', 'phone', 'city', 'lat', 'lng', 'experience_years', 'hourly_rate', 'bio', 'is_verified', 'rating']
        if is_active:
             # Assuming we add is_active later or use a different flag
             pass

        if min_rating:
            query = query.gte("rating", min_rating)
        
        if max_price:
            query = query.lte("hourly_rate", max_price)

        result = query.execute()
        workers = result.data or []
            
        return workers

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
        
        return result.data[0] if result.data else None

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

