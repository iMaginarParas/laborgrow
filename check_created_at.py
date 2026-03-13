from database import supabase

def check_created_at():
    try:
        res = supabase.table("bookings").select("created_at").limit(1).execute()
        print("created_at EXISTS")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_created_at()
