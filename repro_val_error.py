import uuid
from pydantic import ValidationError
from models.schemas import BookingResponse, WorkerResponse
from datetime import datetime

def test_validation():
    print("🧪 Testing Pydantic validation for BookingResponse...")
    
    # Simulate the raw dictionary that might be causing the error
    # Note: skills is None here
    worker_data = {
        "id": uuid.uuid4(),
        "bio": "Test bio",
        "city": "Noida",
        "lat": 0.0,
        "lng": 0.0,
        "experience_years": 5,
        "hourly_rate": 500.0,
        "rating": 4.5,
        "is_verified": True,
        "is_available": True,
        "user": {
            "id": uuid.uuid4(),
            "name": "Test Worker",
            "email": "worker@test.com",
            "phone": "1234567890",
            "created_at": datetime.now()
        },
        "categories": [],
        "skills": None  # This is the culprit!
    }
    
    booking_data = {
        "id": uuid.uuid4(),
        "worker": worker_data,
        "booking_date": "2026-03-15",
        "time_slot": "10:00 AM",
        "hours": 2,
        "address": "Test Address",
        "total_amount": 1050.0,
        "platform_fee": 50.0,
        "discount_amount": 0.0,
        "status": "pending",
        "booking_ref": "LBG-TEST",
        "created_at": datetime.now()
    }
    
    try:
        BookingResponse(**booking_data)
        print("✅ Validation passed unexpectedly!")
    except ValidationError as e:
        print("❌ Validation failed as expected:")
        print(e)
        for error in e.errors():
            print(f"  Field: {error['loc']}, Type: {error['type']}, Input: {error.get('input')}")

if __name__ == "__main__":
    test_validation()
