from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from database import get_db
from models.models import User
from models.schemas import UserCreate, Token, LoginRequest, UserResponse
from services.auth_service import AuthService
from dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["User Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Onboard a new user with standard LaborGrow validation and encryption.
    """
    try:
        new_user = await AuthService.register_user(db, user_in)
        return new_user
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest, 
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Verify identity and issue JWT access and refresh tokens.
    """
    user = await AuthService.authenticate_user(db, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid contact info or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Fetch details of the currently authorized user context.
    """
    return current_user
