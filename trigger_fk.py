from database import supabase

def get_constraints():
    print("Listing foreign keys for 'bookings'...")
    try:
        # Standard query to get foreign keys
        query = """
        SELECT
            tc.constraint_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='bookings';
        """
        # We can't run raw SQL with .rpc() unless it's predefined.
        # But maybe we can try an RPC if it exists.
        # Otherwise, let's just try to infer from data.
        
        # Another trick: insert a random UUID as customer_id 
        # to trigger a foreign key violation that NAMES the target table.
        import uuid
        fake_id = str(uuid.uuid4())
        supabase.table("bookings").insert({
            "customer_id": fake_id, 
            "worker_id": "cf688a6d-feaf-46b6-9026-6081c41ab5e1",
            "category_id": 1,
            "booking_date": "2026-01-01",
            "time_slot": "9 AM",
            "hours": 1,
            "address": "test"
        }).execute()
    except Exception as e:
        print(f"Violation Error: {e}")

if __name__ == "__main__":
    get_constraints()
