from database import supabase

def dump_columns():
    # Try to select a non-existent column to get the list of valid ones in error
    try:
        supabase.table("bookings").select("non_existent_column").limit(1).execute()
    except Exception as e:
        print(f"Error Message: {e}")

if __name__ == "__main__":
    dump_columns()
