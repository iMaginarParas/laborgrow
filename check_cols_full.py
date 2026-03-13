from database import supabase

def check_all_cols():
    cols = [
        "id", "customer_id", "worker_id", "category_id", 
        "booking_date", "time_slot", "hours", "address", 
        "total_amount", "platform_fee", "discount_amount", 
        "status", "booking_ref", "created_at"
    ]
    for c in cols:
        try:
            supabase.table("bookings").select(c).limit(1).execute()
            print(f"Col {c}: OK")
        except Exception as e:
            print(f"Col {c}: MISSING or ERROR ({e})")

if __name__ == "__main__":
    check_all_cols()
