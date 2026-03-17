from database import init_supabase
c = init_supabase()
r = c.table('jobs').select('*').limit(1).execute()
if r.data:
    for key in sorted(r.data[0].keys()):
        print(f"COL: {key}")
else:
    print("No Data")
