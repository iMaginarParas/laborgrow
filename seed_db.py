import asyncio
import os
import sys
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the project root to sys.path
sys.path.append(os.getcwd())

from database import SessionLocal, Base, engine
from models.models import User, Worker, Category, WorkerSkill, worker_categories
from services.auth_service import AuthService

async def seed_data():
    print("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        async with session.begin():
            print("Seeding categories...")
            cats = [
                Category(name="Painting", emoji="🎨", slug="painting"),
                Category(name="Plumbing", emoji="🔧", slug="plumbing"),
                Category(name="Electrical", emoji="⚡", slug="electrical"),
                Category(name="Carpentry", emoji="🪚", slug="carpentry"),
                Category(name="Cleaning", emoji="🧹", slug="cleaning"),
                Category(name="Gardening", emoji="🌿", slug="gardening"),
                Category(name="AC Repair", emoji="❄️", slug="ac-repair"),
            ]
            session.add_all(cats)
            await session.flush() # Populate IDs

            print("Seeding customer...")
            customer = User(
                id=uuid.uuid4(),
                name="Test Customer",
                email="test@example.com",
                phone="9999999999",
                password_hash=AuthService.get_password_hash("test1234"),
                city="Bengaluru"
            )
            session.add(customer)

            print("Seeding workers...")
            # Worker 1: Painter
            u1_id = uuid.uuid4()
            u1 = User(id=u1_id, name="Rahul Sharma", email="rahul@example.com", phone="8888888881", password_hash=AuthService.get_password_hash("test1234"), city="Bengaluru")
            session.add(u1)
            w1 = Worker(
                id=uuid.uuid4(), user_id=u1_id, bio="Expert in interior and texture painting.",
                city="Bengaluru", lat=12.9716, lng=77.5946, experience_years=8, hourly_rate=350,
                is_verified=True, rating=4.9
            )
            w1.categories.append(cats[0]) # Painting
            session.add(w1)
            session.add_all([WorkerSkill(worker=w1, skill_name=s) for s in ["Interior Painting", "Stencil Art", "Wall Putty"]])

            # Worker 2: Plumber
            u2_id = uuid.uuid4()
            u2 = User(id=u2_id, name="Amit Patel", email="amit@example.com", phone="8888888882", password_hash=AuthService.get_password_hash("test1234"), city="Bengaluru")
            session.add(u2)
            w2 = Worker(
                id=uuid.uuid4(), user_id=u2_id, bio="Specialist in leakage repairs and bathroom fittings.",
                city="Bengaluru", lat=12.9800, lng=77.6000, experience_years=5, hourly_rate=450,
                is_verified=True, rating=4.7
            )
            w2.categories.append(cats[1]) # Plumbing
            session.add(w2)
            session.add_all([WorkerSkill(worker=w2, skill_name=s) for s in ["Leakage Fix", "Pipe Fitting", "Tap Repair"]])

            # Worker 3: Electrician
            u3_id = uuid.uuid4()
            u3 = User(id=u3_id, name="Vikram Singh", email="vikram@example.com", phone="8888888883", password_hash=AuthService.get_password_hash("test1234"), city="Bengaluru")
            session.add(u3)
            w3 = Worker(
                id=uuid.uuid4(), user_id=u3_id, bio="Handling all residential electrical issues.",
                city="Bengaluru", lat=12.9500, lng=77.5800, experience_years=10, hourly_rate=400,
                is_verified=True, rating=4.8
            )
            w3.categories.append(cats[2]) # Electrical
            session.add(w3)
            session.add_all([WorkerSkill(worker=w3, skill_name=s) for s in ["Short Circuit Fix", "Fan Installation", "Wiring"]])

            print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
