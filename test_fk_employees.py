from database import supabase
import uuid

def test_non_employee_user():
    print("Testing if customer_id must be in 'employees' table...")
    # Generate a random valid UUID that is NOT in any table
    random_user_id = str(uuid.uuid4())
    try:
        supabase.table("bookings").insert({
            "id": str(uuid.uuid4()),
            "customer_id": random_user_id, 
            "worker_id": "cf688a6d-feaf-46b6-9026-6081c41ab5e1",
            "category_id": 1,
            "booking_date": "2026-01-01",
            "time_slot": "9 AM",
            "hours": 1,
            "address": "test",
            "total_amount": 550.0,
            "platform_fee": 50.0,
            "discount_amount": 0.0,
            "booking_ref": "FK-TEST-2",
            "status": "pending"
        }).execute()
        print("✅ SUCCESS: customer_id doesn't need to be in 'employees'")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    test_non_employee_user()
