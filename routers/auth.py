from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from database import get_supabase
from models.schemas import UserCreate, Token, LoginRequest, UserResponse
from services.auth_service import AuthService
from dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["User Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate
) -> Dict[str, Any]:
    """
    Onboard a new user using Supabase Auth and professional profile creation.
    """
    return await AuthService.register_user(user_in)

@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest
) -> Token:
    """
    Verify identity via Supabase and return access/refresh tokens.
    """
    auth_data = await AuthService.authenticate_user(credentials)
    
    return {
        "access_token": auth_data["access_token"],
        "refresh_token": auth_data["refresh_token"],
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Any:
    """
    Fetch details of the currently authorized user context from Supabase.
    """
    # current_user from dependency is expected to be the profile data or user object
    profile = await AuthService.get_user_profile(str(current_user["id"]))
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile
@router.put("/me", response_model=UserResponse)
async def update_me(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update details of the currently authorized user.
    """
    profile = await AuthService.update_user_profile(str(current_user["id"]), updates)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile
