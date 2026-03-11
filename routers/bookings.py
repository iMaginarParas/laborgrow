from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import uuid

from database import get_supabase
from models.schemas import BookingCreate, BookingResponse
from dependencies.auth import get_current_user
from services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings Ecosystem"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Establish a new job booking on the platform using Supabase.
    Auth requirement: Valid Customer account.
    """
    try:
        return await BookingService.create_booking(booking_in, current_user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}"
        )

@router.get("", response_model=List[BookingResponse])
async def list_customer_bookings(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[BookingResponse]:
    """
    Fetch history of bookings for the authorized user from Supabase.
    """
    return await BookingService.list_customer_bookings(current_user["id"])

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_detail(
    booking_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Detailed status and overview of a specific booking instance.
    """
    booking = await BookingService.get_booking_detail(str(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking record not found.")
    
    # Ownership authorization check
    if str(booking["customer_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    return booking

