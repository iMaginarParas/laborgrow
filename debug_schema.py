from database import supabase
import json

def get_detailed_schema():
    print("Fetching bookings table structure...")
    try:
        # Querying information_schema for columns
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'bookings'
        ORDER BY ordinal_position;
        """
        # Note: supabase.rpc() or raw SQL might be restricted. 
        # Let's try to get one row and look at keys if available, 
        # OR try to catch a detailed error message.
        
        # Test 1: Insert empty dict to trigger column list in error
        res = supabase.table("bookings").insert({}).execute()
        print(f"Result: {res.data}")
    except Exception as e:
        print(f"Detailed Error: {e}")

if __name__ == "__main__":
    get_detailed_schema()
