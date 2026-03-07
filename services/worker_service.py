from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from models.models import Worker, Category, worker_categories

class WorkerService:
    """
    Coordinator for the supply-side of the marketplace (Workers/Categories).
    """

    @staticmethod
    async def list_workers(
        db: AsyncSession,
        category_slug: Optional[str] = None,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        is_active: bool = True
    ) -> List[Worker]:
        """
        Query the worker pool with multi-criteria filtering.
        """
        stmt = select(Worker).options(
            selectinload(Worker.user),
            selectinload(Worker.categories),
            selectinload(Worker.skills)
        ).filter(Worker.is_active == is_active)

        # Dynamic Filtering
        if category_slug:
            stmt = stmt.join(Worker.categories).filter(Category.slug == category_slug)
        
        if min_rating:
            stmt = stmt.filter(Worker.rating >= min_rating)
        
        if max_price:
            stmt = stmt.filter(Worker.hourly_rate <= max_price)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_worker_detail(
        db: AsyncSession, 
        worker_id: uuid.UUID
    ) -> Optional[Worker]:
        """
        Fetch worker with full profile and skills metadata.
        """
        stmt = select(Worker).options(
            selectinload(Worker.user),
            selectinload(Worker.categories),
            selectinload(Worker.skills)
        ).filter(Worker.id == worker_id)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_categories(db: AsyncSession) -> List[Category]:
        """
        Retrieve all marketplace service categories.
        """
        stmt = select(Category)
        result = await db.execute(stmt)
        return result.scalars().all()
