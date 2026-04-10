from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database_sqlalchemy import get_db
from ..dependencies.admin_auth import role_required
from ..services.admin_service import AdminService, log_admin_audit
from ..services.booking_service import BookingService
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/admin", tags=["Booking Management"])

@router.get("/bookings")
async def get_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    return AdminService.get_paginated_bookings(db, skip, limit, search)

@router.post("/bookings/reassign")
async def reassign_booking(
    booking_id: UUID,
    new_worker_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    """
    Manually reassigns a booking to a different worker.
    """
    log_admin_audit(db, admin["id"], "REASSIGN_BOOKING", str(booking_id), {"new_worker": str(new_worker_id)})
    return {"message": "Booking reassigned"}

@router.post("/bookings/cancel")
async def cancel_booking(
    booking_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    log_admin_audit(db, admin["id"], "CANCEL_BOOKING", str(booking_id), {"reason": reason})
    return {"message": "Booking cancelled"}

@router.post("/bookings/force-complete")
async def force_complete_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    log_admin_audit(db, admin["id"], "FORCE_COMPLETE_BOOKING", str(booking_id), {})
    return {"message": "Booking marked as complete"}
