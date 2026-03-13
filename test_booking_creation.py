import asyncio
import uuid
from database import supabase
from services.booking_service import BookingService
from models.schemas import BookingCreate

async def test_booking():
    print("🧪 Running internal booking test...")
    
    # Use real worker ID from employees table
    worker_id = "cf688a6d-feaf-46b6-9026-6081c41ab5e1" # DARSHAN URS
    # Use real user ID
    user_id = "e2867f01-6e68-44da-9f30-56443add56df" # X
    
    current_user = {
        "id": user_id,
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"}
    }
    
    booking_in = BookingCreate(
        worker_id=uuid.UUID(worker_id),
        category_id=1,
        booking_date="2026-03-15",
        time_slot="10:00 AM",
        hours=2,
        address="Test Address, Noida"
    )
    
    try:
        print(f"Attempting to create booking for worker {worker_id} by user {user_id}...")
        result = await BookingService.create_booking(booking_in, current_user)
        print("✅ Booking successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Booking failed with error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_booking())
