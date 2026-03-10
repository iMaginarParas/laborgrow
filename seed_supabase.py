import uuid
import os
from dotenv import load_dotenv
from supabase import create_client
from database import supabase as public_supabase

load_dotenv()

# Admin client for Auth management
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
admin_supabase = create_client(SUPABASE_URL, SERVICE_KEY)

def seed_marketplace_data():
    print("🚀 Starting marketplace data seed with Auth users...")

    # 1. Seed Categories
    categories = [
        {"name": "Plumbing", "slug": "plumbing", "icon_url": "https://cdn-icons-png.flaticon.com/512/3015/3015143.png"},
        {"name": "Electrical", "slug": "electrical", "icon_url": "https://cdn-icons-png.flaticon.com/512/3105/3105807.png"},
        {"name": "Cleaning", "slug": "cleaning", "icon_url": "https://cdn-icons-png.flaticon.com/512/2954/2954893.png"}
    ]
    try:
        public_supabase.table("categories").upsert(categories, on_conflict="slug").execute()
        print("✅ Categories seeded.")
    except Exception as e:
        print(f"⚠️ Categories skipped: {e}")

    # 2. Seed Real Auth Users & Employees
    test_workers = [
        {
            "full_name": "Rajesh Plumber",
            "email": "rajesh@laborgrow.com",
            "phone": "+919876543210",
            "password": "password123",
            "city": "Mumbai",
            "hourly_rate": 450.0
        },
        {
            "full_name": "Test User",
            "email": "test@laborgrow.com",
            "phone": "+919999999999", # Matches the screenshot
            "password": "password123", # Default common password
            "city": "Pune",
            "hourly_rate": 500.0
        },
        {
            "full_name": "Admin User",
            "email": "admin@laborgrow.com",
            "phone": "+911234567890",
            "password": "password123",
            "city": "Mumbai",
            "hourly_rate": 1000.0
        }
    ]

    for data in test_workers:
        try:
            print(f"Creating Auth user for {data['email']}...")
            # Create in Supabase Auth
            auth_user = admin_supabase.auth.admin.create_user({
                "email": data["email"],
                "phone": data["phone"],
                "password": data["password"],
                "email_confirm": True,
                "phone_confirm": True,
                "user_metadata": {"name": data["full_name"], "role": "employee"}
            })

            # Sync to public.employees
            employee_profile = {
                "id": auth_user.user.id,
                "full_name": data["full_name"],
                "email": data["email"],
                "phone": data["phone"],
                "city": data["city"],
                "hourly_rate": data["hourly_rate"],
                "is_verified": True,
                "rating": 4.5
            }
            public_supabase.table("employees").upsert(employee_profile, on_conflict="id").execute()
            print(f"✅ User {data['email']} created and synced.")
        except Exception as e:
            print(f"⚠️ User {data['email']} skipped (might already exist): {e}")

    # 3. Seed Jobs
    sample_jobs = [
        {"title": "Industrial Wiring", "description": "Need expert for factory wiring.", "job_city": "Mumbai", "salary_min": 5000, "salary_max": 15000}
    ]
    try:
        public_supabase.table("jobs").upsert(sample_jobs).execute()
        print("✅ Jobs seeded.")
    except Exception as e:
        print(f"⚠️ Jobs skipped: {e}")

    print("\n🏁 Seeding process complete!")

if __name__ == "__main__":
    seed_marketplace_data()
