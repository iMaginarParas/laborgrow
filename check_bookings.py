from database import supabase
import json

def check_bookings_table():
    print("Checking 'bookings' table...")
    try:
        # Try to fetch one row to see columns
        res = supabase.table("bookings").select("*").limit(1).execute()
        if res.data:
            print(f"Columns: {list(res.data[0].keys())}")
        else:
            print("Table is empty. Checking schema via RPC if possible (unlikely)...")
            # Try a dummy insert that should fail but might show columns in error
            try:
                supabase.table("bookings").insert({"invalid_column_name": "test"}).execute()
            except Exception as e:
                print(f"Insert error (might show columns): {e}")

    except Exception as e:
        print(f"Error checking table: {e}")

if __name__ == "__main__":
    check_bookings_table()
