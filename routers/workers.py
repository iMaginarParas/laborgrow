from fastapi import APIRouter, Depends, Query, HTTPException
import uuid
from typing import List, Optional

from database import get_supabase
from models.schemas import WorkerResponse, CategoryResponse
from services.worker_service import WorkerService

router = APIRouter(prefix="/workers", tags=["Workers Pool"])
cat_router = APIRouter(prefix="/categories", tags=["Service Categories"])

@router.get("", response_model=List[WorkerResponse])
async def list_workers(
    category: Optional[str] = Query(None, description="Category filter by slug"),
    lat: Optional[float] = Query(None, description="Supply search latitude"),
    lng: Optional[float] = Query(None, description="Supply search longitude"),
    radius: Optional[float] = Query(10.0, description="Radial distance limit"),
    min_rating: float = Query(0.0, description="Minimum star rating filter"),
    max_price: Optional[float] = Query(None, description="Maximum cost per hour filter"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    search: Optional[str] = Query(None, description="Search by name, skill, or category")
) -> List[WorkerResponse]:
    """
    Explore available service providers on the LaborGrow marketplace using Supabase.
    """
    return await WorkerService.list_workers(
        category, min_rating, max_price, city, available, search
    )

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker_detail(
    worker_id: uuid.UUID
) -> WorkerResponse:
    """
    Get the professional profile and skill set for a specific worker.
    """
    worker = await WorkerService.get_worker_detail(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found.")
    return worker

@cat_router.get("", response_model=List[CategoryResponse])
async def list_categories() -> List[CategoryResponse]:
    """
    Discover all job categories mapped in the platform.
    """
    return await WorkerService.list_categories()

