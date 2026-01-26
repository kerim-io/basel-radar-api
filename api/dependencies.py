from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import JWTError
from typing import Optional

from db.database import get_async_session
from db.models import User
from services.auth_service import decode_access_token

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

# Rate limiter - uses client IP address for identification
limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get current authenticated user from JWT access token.

    Validates:
    - Token signature and expiration
    - Token type is 'access' (not refresh)
    - User exists and is active
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception
    except (ValueError, TypeError):
        raise credentials_exception


async def get_admin_user(
    request: Request,
    admin_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get current admin user from session cookie.

    Validates:
    - Token exists in cookie
    - Token is valid JWT
    - User exists, is active, and is_admin=True

    Returns 403 if user is not an admin.
    """
    redirect_exception = HTTPException(
        status_code=status.HTTP_302_FOUND,
        detail="Not authenticated",
        headers={"Location": "/admin/login"}
    )

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )

    if not admin_token:
        raise redirect_exception

    try:
        payload = decode_access_token(admin_token)
        user_id = int(payload.get("sub"))

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise redirect_exception

        if not user.is_admin:
            raise forbidden_exception

        return user

    except JWTError:
        raise redirect_exception
    except (ValueError, TypeError):
        raise redirect_exception
