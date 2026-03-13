from database import supabase
import uuid

def trigger_fk():
    print("Testing 'bookings' constraints with fake user ID...")
    fake_id = str(uuid.uuid4())
    try:
        supabase.table("bookings").insert({
            "id": str(uuid.uuid4()),
            "customer_id": fake_id, 
            "worker_id": "cf688a6d-feaf-46b6-9026-6081c41ab5e1",
            "category_id": 1,
            "booking_date": "2026-01-01",
            "time_slot": "9 AM",
            "hours": 1,
            "address": "test",
            "total_amount": 550.0,
            "platform_fee": 50.0,
            "discount_amount": 0.0,
            "booking_ref": "TRIG-FK-TEST",
            "status": "pending"
        }).execute()
    except Exception as e:
        print(f"Violation Response: {e}")

if __name__ == "__main__":
    trigger_fk()
