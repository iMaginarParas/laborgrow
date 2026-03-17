from database import init_supabase
import uuid
c = init_supabase()
job_data = {
    "title": "Test Painter Job v3",
    "description": "Looking for a test painter for 5 days.",
    "category_id": 1,
    "job_city": "Noida",
    "salary_min": 500.0,
    "salary_max": 1000.0,
    "openings": 1,
    "employer_id": "f22c62a6-f526-4833-a92a-70ee76d607f7",
    "status": "open",
    "lat_long": "POINT(77.3 28.5)"
}
try:
    r = c.table('jobs').insert(job_data).execute()
    print(f"SUCCESS: {r.data}")
except Exception as e:
    print(f"ERROR: {e}")
