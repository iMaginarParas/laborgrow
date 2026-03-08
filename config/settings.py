from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    """
    Centralized configuration management for the LaborGrow production API.
    Handles environment variables and application-wide constants.
    """
    # Core Metadata
    PROJECT_NAME: str = "LaborGrow Production API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Internal Security
    SECRET_KEY: str = "super-secret-key-change-me-in-production"
    ADMIN_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google Maps Integration
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    
    # External Payment (Razorpay)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """
        Ensures the database URL is compatible with asyncpg.
        Railway and other providers often use 'postgres://', but asyncpg requires 'postgresql+asyncpg://'.
        """
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        # Also handle cases where it might start with postgresql:// but missing the +asyncpg
        if v and v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
