import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import jwt
from app.core.config import settings
from app.core.exceptions import UnauthorizedError

class UserRole:
    ADMIN = "ADMIN"
    DISTRICT_ADMIN = "DISTRICT_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT = "PARENT"

    ALL_ROLES = [ADMIN, DISTRICT_ADMIN, TEACHER, STUDENT, PARENT]

def create_access_token(
    user_id: str,
    role: str,
    school_id: Optional[str] = None,
    district_id: Optional[str] = None,
    name: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generates a signed JWT access token containing standard RBAC claims."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload: Dict[str, Any] = {
        "sub": user_id,
        "user_id": user_id,
        "role": role,
        "school_id": school_id,
        "district_id": district_id,
        "name": name,
        "token_type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
    }
    
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def create_refresh_token(user_id: str) -> str:
    """Generates a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": user_id,
        "user_id": user_id,
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates JWT signature and expiration."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(message="Token has expired", code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(message=f"Invalid token: {str(e)}", code="INVALID_TOKEN")
