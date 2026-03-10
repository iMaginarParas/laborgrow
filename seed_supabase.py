import uuid
from database import supabase

def seed_marketplace_data():
    print("🚀 Starting marketplace data seed...")

    # 1. Seed Categories (if table exists)
    categories = [
        {"name": "Plumbing", "slug": "plumbing", "icon_url": "https://cdn-icons-png.flaticon.com/512/3015/3015143.png"},
        {"name": "Electrical", "slug": "electrical", "icon_url": "https://cdn-icons-png.flaticon.com/512/3105/3105807.png"},
        {"name": "Cleaning", "slug": "cleaning", "icon_url": "https://cdn-icons-png.flaticon.com/512/2954/2954893.png"},
        {"name": "Carpentry", "slug": "carpentry", "icon_url": "https://cdn-icons-png.flaticon.com/512/2415/2415302.png"}
    ]

    try:
        print("Inserting categories...")
        supabase.table("categories").upsert(categories, on_conflict="slug").execute()
        print("✅ Categories seeded.")
    except Exception as e:
        print(f"⚠️ Could not seed categories (Table might be missing): {e}")

    # 2. Seed Sample Employees (Workers)
    # We use existing or new UUIDs for employees
    sample_employees = [
        {
            "id": str(uuid.uuid4()),
            "full_name": "Rajesh Kumar",
            "email": f"rajesh_{uuid.uuid4().hex[:4]}@example.com",
            "phone": "9876543210",
            "city": "Mumbai",
            "hourly_rate": 450.0,
            "rating": 4.8,
            "bio": "Expert plumber with 10 years of experience in residential and commercial repairs.",
            "is_verified": True,
            "lat": 19.0760,
            "lng": 72.8777
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Priya Sharma",
            "email": f"priya_{uuid.uuid4().hex[:4]}@example.com",
            "phone": "9876543211",
            "city": "Delhi",
            "hourly_rate": 600.0,
            "rating": 4.9,
            "bio": "Certified electrician specializing in smart home installations and wiring.",
            "is_verified": True,
            "lat": 28.6139,
            "lng": 77.2090
        }
    ]

    try:
        print("Inserting sample employees...")
        supabase.table("employees").upsert(sample_employees, on_conflict="email").execute()
        print("✅ Employees seeded.")
    except Exception as e:
        print(f"❌ Failed to seed employees: {e}")

    # 3. Seed Sample Jobs
    sample_jobs = [
        {
            "title": "Fix Leaking Pipe",
            "description": "Kitchen sink pipe is leaking, needs immediate repair.",
            "job_city": "Mumbai",
            "salary_min": 500,
            "salary_max": 2000,
            "lat": 19.0760,
            "lng": 72.8777,
            "status": "open"
        },
        {
            "title": "Home Cleaning Service",
            "description": "Deep cleaning for a 3BHK apartment required this weekend.",
            "job_city": "Delhi",
            "salary_min": 1500,
            "salary_max": 5000,
            "lat": 28.6139,
            "lng": 77.2090,
            "status": "open"
        }
    ]

    try:
        print("Inserting sample jobs...")
        supabase.table("jobs").upsert(sample_jobs).execute()
        print("✅ Jobs seeded.")
    except Exception as e:
        print(f"❌ Failed to seed jobs: {e}")

    print("\n🏁 Seeding process finished!")

if __name__ == "__main__":
    seed_marketplace_data()
