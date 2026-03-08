from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings
from supabase import create_client, Client

# Async engine for efficient database connections
# We use a placeholder if DATABASE_URL is empty to prevent startup crashes during deployment
DB_URL = settings.DATABASE_URL or "postgresql+asyncpg://placeholder:placeholder@localhost:5432/placeholder"

engine = create_async_engine(DB_URL, echo=False)

# Session factory for route-scoped transactions
SessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Shared Supabase specialized client for direct integration features
# Supabase client is also made resilient to empty credentials
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
else:
    supabase = None

class Base(DeclarativeBase):
    """
    Standard declarative base used across all SQLAlchemy models.
    """
    pass

async def get_db():
    """
    FastAPI dependency yielding a thread-safe async database session.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
