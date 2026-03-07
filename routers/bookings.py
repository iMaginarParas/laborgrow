from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from database import get_db
from models.models import User
from models.schemas import BookingCreate, BookingResponse
from dependencies.auth import get_current_user
from services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings Ecosystem"])

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """
    Establish a new job booking on the platform.
    Auth requirement: Valid Customer account.
    """
    try:
        return await BookingService.create_booking(db, booking_in, current_user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )

@router.get("/", response_model=List[BookingResponse])
async def list_customer_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[BookingResponse]:
    """
    Fetch history of bookings for the authorized user.
    """
    return await BookingService.list_customer_bookings(db, current_user.id)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_detail(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """
    Detailed status and overview of a specific booking instance.
    """
    booking = await BookingService.get_booking_detail(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking record not found.")
    
    # Ownership authorization check
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    return booking
