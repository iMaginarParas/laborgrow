from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from database import get_supabase

# Using HTTPBearer to support standard Bearer token headers from Flutter/Client
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to validate the Supabase JWT in the Request Authorization header
    and return the current user profile/metadata.
    """
    token = credentials.credentials
    try:
        client = await get_supabase()
        # Validate the token with Supabase Auth
        user_response = await client.auth.get_user(token)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # We return the user object as a dictionary-like structure for consistency
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "user_metadata": user_response.user.user_metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

