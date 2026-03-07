from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings
from supabase import create_client, Client

# Async engine for efficient database connections
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Session factory for route-scoped transactions
SessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Shared Supabase specialized client for direct integration features
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

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
