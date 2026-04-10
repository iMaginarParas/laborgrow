from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.admin_security import SECRET_KEY, ALGORITHM, TokenData
from database import get_supabase
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    
    client = get_supabase()
    # Join with admin_roles to get the actual role name string
    admin_res = client.table("admin_users") \
        .select("*, admin_roles(name)") \
        .eq("email", token_data.email) \
        .eq("is_active", True) \
        .execute()
        
    if not admin_res.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin account inactive or not found"
        )
        
    admin = admin_res.data[0]
    # Simplify structure for downstream usage
    admin["role"] = admin["admin_roles"]["name"]
    return admin

def role_required(allowed_roles: List[str]):
    """
    Dependency factory to enforce Role-Based Access Control.
    """
    def role_checker(current_admin: dict = Depends(get_current_admin)):
        if current_admin["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}"
            )
        return current_admin
    return role_checker
