import random
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from models.models import Booking, Worker, User
from models.schemas import BookingCreate

class BookingService:
    """
    Business logic coordinator for the booking lifecycle:
    pricing -> validation -> database transaction.
    """

    @staticmethod
    def calculate_pricing(
        hourly_rate: float, 
        hours: int, 
        is_first_booking: bool = False
    ) -> Dict[str, float]:
        """
        Standard LaborGrow pricing model: (Rate * Hours) + ₹50 fee - 20% discount (on first booking).
        """
        base_amount = hourly_rate * hours
        platform_fee = 50.0  # Fixed marketplace platform fee
        discount = base_amount * 0.20 if is_first_booking else 0.0
        total = base_amount + platform_fee - discount
        
        return {
            "base_amount": base_amount,
            "platform_fee": platform_fee,
            "discount_amount": discount,
            "total_amount": total
        }

    @staticmethod
    def generate_booking_ref() -> str:
        """
        Secure and human-readable reference code.
        """
        year = datetime.now().year
        rand_id = random.randint(1000, 9999)
        return f"LBG-{year}-{rand_id}"

    @staticmethod
    async def create_booking(
        db: AsyncSession, 
        booking_in: BookingCreate, 
        current_user: User
    ) -> Booking:
        """
        Process a new booking transaction. Validates worker presence and computes production-grade pricing.
        """
        # 1. Fetch target worker details
        result = await db.execute(select(Worker).filter(Worker.id == booking_in.worker_id))
        worker = result.scalar_one_or_none()
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified worker not found.")

        # 2. Check for onboarding discount eligibility
        count_stmt = select(func.count()).select_from(Booking).filter(Booking.customer_id == current_user.id)
        bookings_count = await db.execute(count_stmt)
        is_first = bookings_count.scalar() == 0
        
        # 3. Finalize Pricing
        pricing = BookingService.calculate_pricing(
            hourly_rate=worker.hourly_rate,
            hours=booking_in.hours,
            is_first_booking=is_first
        )

        # 4. Persistence
        new_booking = Booking(
            customer_id=current_user.id,
            worker_id=booking_in.worker_id,
            category_id=booking_in.category_id,
            booking_date=booking_in.booking_date,
            time_slot=booking_in.time_slot,
            hours=booking_in.hours,
            address=booking_in.address,
            total_amount=pricing["total_amount"],
            platform_fee=pricing["platform_fee"],
            discount_amount=pricing["discount_amount"],
            booking_ref=BookingService.generate_booking_ref(),
            status="pending"
        )
        
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        
        # 5. Return detailed view
        return await BookingService.get_booking_detail(db, new_booking.id)

    @staticmethod
    async def get_booking_detail(
        db: AsyncSession, 
        booking_id: uuid.UUID
    ) -> Optional[Booking]:
        """
        Fetch booking with full relationship hydration (Worker, User, Categories).
        """
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.worker).selectinload(Worker.user),
                selectinload(Booking.worker).selectinload(Worker.categories),
                selectinload(Booking.worker).selectinload(Worker.skills)
            )
            .filter(Booking.id == booking_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_customer_bookings(
        db: AsyncSession, 
        customer_id: uuid.UUID
    ) -> List[Booking]:
        """
        Optimized query for retrieving history for a specific customer.
        """
        stmt = (
            select(Booking)
            .filter(Booking.customer_id == customer_id)
            .order_by(Booking.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()
