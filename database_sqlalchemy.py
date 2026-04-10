from sqlalchemy import create_client, create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# We assume DATABASE_URL is available in .env as per most FastAPI setups
# If not, it can be constructed from Supabase parameters
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Fallback to a placeholder if not found, though in production this must be set
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
