import asyncio
import os
import sys
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

from database import supabase
from config.settings import settings

async def seed_jobs():
    print("Seeding dummy jobs into Supabase...")
    
    # Check if SUPABASE_URL and KEY are set
    if "your-project-id" in settings.SUPABASE_URL or "your-service-role-key" in settings.SUPABASE_KEY:
        print("❌ ERROR: Supabase credentials are not set in .env")
        print("Please update SUPABASE_URL and SUPABASE_KEY in your .env file before running this script.")
        return

    dummy_jobs = [
        {
            "title": "Home Deep Cleaning",
            "description": "Require deep cleaning for a 3BHK apartment in Koramangala.",
            "lat": 12.9352,
            "lng": 77.6245,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Kitchen Plumbing Issue",
            "description": "Sink pipe leaking, need urgent repair in Indiranagar.",
            "lat": 12.9784,
            "lng": 77.6408,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Garden Maintenance",
            "description": "Monthly lawn mowing and plant pruning in HSR Layout.",
            "lat": 12.9100,
            "lng": 77.6450,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Living Room Painting",
            "description": "Single wall texture painting project in Whitefield.",
            "lat": 12.9698,
            "lng": 77.7499, # This is further away, might be > 10km depending on worker location
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "AC Not Cooling",
            "description": "General service and gas refilling needed in Jayanagar.",
            "lat": 12.9300,
            "lng": 77.5800,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Electrical Rewiring",
            "description": "Small office rewiring project in MG Road area.",
            "lat": 12.9750,
            "lng": 77.5900,
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    try:
        # Insert jobs into Supabase
        response = supabase.table("jobs").insert(dummy_jobs).execute()
        print(f"✅ Successfully seeded {len(dummy_jobs)} jobs!")
    except Exception as e:
        print(f"❌ Failed to seed jobs: {e}")
        print("\nMake sure the 'jobs' table exists in your Supabase database with columns:")
        print("title (text), description (text), lat (float8), lng (float8), created_at (timestamp)")

if __name__ == "__main__":
    asyncio.run(seed_jobs())
