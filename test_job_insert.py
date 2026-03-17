from database import init_supabase
import uuid
c = init_supabase()
job_data = {
    "title": "Test Painter Job",
    "description": "Looking for a test painter for 5 days.",
    "category_id": 1,
    "job_city": "Noida",
    "salary_min": 500,
    "salary_max": 1000,
    "openings": 1,
    "employer_id": "00000000-0000-0000-0000-000000000000", # Using a dummy UUID for test
    "status": "open"
}
try:
    r = c.table('jobs').insert(job_data).execute()
    print(f"SUCCESS: {r.data}")
except Exception as e:
    print(f"ERROR: {e}")
