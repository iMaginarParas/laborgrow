from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from dependencies.auth import get_current_user
from services.review_service import ReviewService
from models.schemas import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews & Ratings"])

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_in: ReviewCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Leave a review for a worker.
    """
    return await ReviewService.leave_review(
        str(review_in.worker_id), 
        current_user["id"], 
        review_in.rating, 
        review_in.comment
    )

@router.get("/worker/{worker_id}", response_model=List[ReviewResponse])
async def list_worker_reviews(worker_id: str) -> Any:
    """
    Fetch all reviews for a specific worker.
    """
    return await ReviewService.list_worker_reviews(worker_id)
