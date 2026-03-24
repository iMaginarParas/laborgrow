from database import get_supabase
supabase = get_supabase()

tables = ['employees', 'employers', 'jobs', 'job_applications', 'workers', 'categories', 'users', 'bookings']

for t in tables:
    try:
        res = supabase.table(t).select('*').limit(1).execute()
        cols = list(res.data[0].keys()) if res.data else "Empty"
        print(f"{t}: OK | {cols}")
    except Exception as e:
        # Check if the error is "relation does not exist"
        err_msg = str(e)
        if "schema cache" in err_msg or "does not exist" in err_msg:
             print(f"{t}: MISSING")
        else:
             print(f"{t}: ERROR | {err_msg[:50]}")
