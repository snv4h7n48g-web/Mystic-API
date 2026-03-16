"""
FastAPI authentication dependencies.
Provides route protection and user context.
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional
from auth_service import get_auth_service
from user_service import get_user_service


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Dependency to get current authenticated user.
    
    Usage:
        @app.get("/protected")
        def protected_route(user = Depends(get_current_user)):
            return {"user_id": user["id"]}
    
    Args:
        authorization: Authorization header (Bearer token)
        
    Returns:
        User dict
        
    Raises:
        HTTPException 401 if not authenticated
    """
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(401, "Invalid authorization header")
    
    token = parts[1]
    
    # Verify token
    auth_service = get_auth_service()
    user_service = get_user_service()
    
    user_id = user_service.verify_and_refresh_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(401, "User not found")
    
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Allows both authenticated and anonymous access.
    
    Usage:
        @app.get("/optional")
        def optional_route(user = Depends(get_current_user_optional)):
            if user:
                return {"user_id": user["id"]}
            else:
                return {"anonymous": True}
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


async def require_admin(
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to require admin role.
    
    Usage:
        @app.get("/admin")
        def admin_route(user = Depends(require_admin)):
            return {"admin_user": user["email"]}
    """
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    return user
