from database import init_supabase
c = init_supabase()
r = c.table('jobs').select('*').limit(1).execute()
if r.data:
    print(list(r.data[0].keys()))
else:
    print("No Data")
