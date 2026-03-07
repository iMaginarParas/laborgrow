from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from config.settings import settings
from models.models import User
from models.schemas import UserCreate, LoginRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """
    High-level business logic for user authentication, passwords, 
    and session management.
    """

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Securely compare a plain text password to its salted hash.
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate a secure bcrypt hash of a given password.
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Issue a new JWT access token sign with LaborGrow's HMAC signature.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """
        Longer expiration token to support seamless session recovery.
        """
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = data.copy()
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        """
        Coordinate user registration: uniqueness checks, password hashing, and DB save.
        """
        # Validate uniqueness of identifiers
        stmt = select(User).filter((User.email == user_in.email) | (User.phone == user_in.phone))
        result = await db.execute(stmt)
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists."
            )
        
        # Create user with hashed credentials
        new_user = User(
            name=user_in.name,
            email=user_in.email,
            phone=user_in.phone,
            password_hash=AuthService.get_password_hash(user_in.password),
            profile_pic_url=user_in.profile_pic_url,
            address=user_in.address,
            city=user_in.city
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, login_in: LoginRequest) -> Optional[User]:
        """
        Validate credentials for login flow.
        """
        # Search by email OR phone
        stmt = select(User).filter(
            (User.email == login_in.phone_or_email) | (User.phone == login_in.phone_or_email)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(login_in.password, user.password_hash):
            return None
        return user
