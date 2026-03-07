import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from database import engine, Base
from models import models # Import models to ensure they are registered with Base

async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
