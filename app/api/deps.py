from typing import Optional, List, Dict, Any, Callable
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.mongodb import get_mongo_db
from app.core.jwt import decode_token, UserRole
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> Dict[str, Any]:
    """Validates JWT bearer token and retrieves user identity from MongoDB."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedError(message="Authentication credentials were not provided", code="NO_AUTH_HEADER")

    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise UnauthorizedError(message="Invalid token payload", code="INVALID_TOKEN_PAYLOAD")

    user_repo = UserRepository(db)
    user = await user_repo.find_by_user_id(user_id)
    if not user:
        # If user was created external to MongoDB or in test, fall back to verified claims
        user = {
            "user_id": user_id,
            "role": payload.get("role", UserRole.STUDENT),
            "school_id": payload.get("school_id"),
            "district_id": payload.get("district_id"),
            "name": payload.get("name", "User"),
            "is_active": True,
        }

    if not user.get("is_active", True):
        raise ForbiddenError(message="User account is deactivated", code="USER_INACTIVE")


    # Attach token claims for fast access
    user["token_role"] = payload.get("role")
    user["token_school_id"] = payload.get("school_id")
    user["token_district_id"] = payload.get("district_id")
    user["token_jti"] = payload.get("jti")
    return user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> Optional[Dict[str, Any]]:
    """Returns authenticated user if bearer token is supplied, or None for public endpoints."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials=credentials, db=db)
    except Exception:
        return None

def require_roles(allowed_roles: List[str]) -> Callable:
    """Enforces role-based access control (RBAC)."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise ForbiddenError(
                message=f"Access denied. Requires one of roles: {', '.join(allowed_roles)} (current: {user_role})",
                code="INSUFFICIENT_PERMISSIONS",
            )
        return current_user
    return role_checker
