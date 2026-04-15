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
        client = get_supabase()
        # Validate the token with Supabase Auth
        user_response = client.auth.get_user(token)
        
        if not user_response or not getattr(user_response, 'user', None):
            print(f"AUTH ERROR: No user in response for token prefix {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        # We return the user object as a dictionary-like structure for consistency
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": getattr(user, 'user_metadata', {})
        }
        
    except Exception as e:
        print(f"AUTH EXCEPTION: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

