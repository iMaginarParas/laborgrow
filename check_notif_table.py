from database import init_supabase

def check_table():
    client = init_supabase()
    try:
        res = client.table('notifications').select('*').limit(1).execute()
        print("SUCCESS: Notifications table exists")
        print(f"COLUMNS: {list(res.data[0].keys()) if res.data else 'TABLE EMPTY'}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_table()
