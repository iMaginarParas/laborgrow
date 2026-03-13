from database import supabase

def check_address_length():
    print("Checking 'address' column max length...")
    # Trick: Try to insert a very long address
    long_addr = "A" * 500
    try:
        supabase.table("bookings").insert({
            "id": "00000000-0000-0000-0000-000000000001",
            "customer_id": "e2867f01-6e68-44da-9f30-56443add56df", 
            "worker_id": "cf688a6d-feaf-46b6-9026-6081c41ab5e1",
            "category_id": 1,
            "booking_date": "2026-01-01",
            "time_slot": "9 AM",
            "hours": 1,
            "address": long_addr,
            "total_amount": 550.0,
            "platform_fee": 50.0,
            "discount_amount": 0.0,
            "booking_ref": "LEN-TEST",
            "status": "pending"
        }).execute()
        print("✅ Address supports 500 chars")
        # Cleanup
        supabase.table("bookings").delete().eq("id", "00000000-0000-0000-0000-000000000001").execute()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_address_length()
