from database import init_supabase, get_supabase
import sys

def setup_db():
    init_supabase()
    supabase = get_supabase()
    
    print("Checking for notifications table...")
    try:
        supabase.table("notifications").select("id").limit(1).execute()
        print("Table 'notifications' already exists.")
    except Exception:
        print("Creating 'notifications' table...")
        # Since we use the python client, we can't directly run SQL, 
        # but we can try to insert a dummy to see if it works or fails.
        # REAL setup should be done in Supabase SQL dashboard.
        print("!!! PLEASE RUN THE SQL PROVIDED IN THE CHAT IN YOUR SUPABASE DASHBOARD !!!")

if __name__ == "__main__":
    setup_db()
