from pydantic import TypeAdapter
from models.schemas import BookingResponse, WorkerResponse
import uuid
from datetime import datetime

def test_validation():
    print("Testing TypeAdapter validation...")
    
    worker_data = {
        "id": str(uuid.uuid4()),
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
            "id": str(uuid.uuid4()),
            "name": "Test Worker",
            "email": "worker@test.com",
            "phone": "1234567890",
            "created_at": datetime.now().isoformat()
        },
        "categories": None,
        "skills": None
    }
    
    booking_data = {
        "id": str(uuid.uuid4()),
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
        "created_at": datetime.now().isoformat()
    }
    
    from typing import List
    adapter = TypeAdapter(List[BookingResponse])
    
    try:
        adapter.validate_python([booking_data])
        print("✅ List validation passed!")
    except Exception as e:
        print("❌ List validation failed:")
        print(e)

if __name__ == "__main__":
    test_validation()
