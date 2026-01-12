from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

from db.database import get_async_session
from db.models import User, RefreshToken
from services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decode_refresh_token,
    TOKEN_TYPE_REFRESH
)
from services.apple_auth import verify_apple_token
from core.config import settings
from api.dependencies import limiter, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class AppleAuthRequest(BaseModel):
    code: str
    redirect_uri: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None  # Email from iOS (Apple only sends on first auth)


class PasscodeAuthRequest(BaseModel):
    passcode: str
    username: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user_id: int
    email: Optional[str]
    has_profile: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/apple", response_model=AuthResponse)
@limiter.limit("10/minute")
async def apple_signin(
    request: Request,
    auth_request: AppleAuthRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Sign in with Apple - validates code with Apple servers"""
    try:
        # Verify Apple token
        apple_data = await verify_apple_token(auth_request.code, auth_request.redirect_uri)
        apple_user_id = apple_data["user_id"]
        # Prefer email from iOS request (Apple sends it), fallback to token email
        email = auth_request.email or apple_data.get("email")

        # Check if user exists
        result = await db.execute(
            select(User).where(User.apple_user_id == apple_user_id)
        )
        user = result.scalar_one_or_none()

        # Create user if doesn't exist
        if not user:
            user = User(
                apple_user_id=apple_user_id,
                email=email,
                username=email.split("@")[0] if email else f"user_{apple_user_id[:8]}",
                first_name=auth_request.given_name,
                last_name=auth_request.family_name,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Update existing user with name if provided and not already set
            updated = False
            if auth_request.given_name and not user.first_name:
                user.first_name = auth_request.given_name
                updated = True
            if auth_request.family_name and not user.last_name:
                user.last_name = auth_request.family_name
                updated = True
            if auth_request.email and not user.email:
                user.email = auth_request.email
                updated = True
            if updated:
                await db.commit()
                await db.refresh(user)

        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token_str = create_refresh_token({"sub": str(user.id)})

        # Store refresh token with timezone-aware datetime
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token_obj)

        # Update user's Apple refresh token
        user.refresh_token = apple_data.get("refresh_token")
        await db.commit()

        # Refresh user to ensure has_profile property has fresh data
        await db.refresh(user)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            has_profile=user.has_profile
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Apple authentication failed: {str(e)}"
        )


@router.post("/passcode", response_model=AuthResponse)
@limiter.limit("10/minute")
async def passcode_auth(
    request: Request,
    auth_request: PasscodeAuthRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Auth with passcode fallback"""
    if auth_request.passcode != settings.AUTH_PASSCODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passcode"
        )

    # Create/get guest user
    username = auth_request.username or f"guest_{datetime.now(timezone.utc).timestamp()}"
    guest_id = f"passcode_{username}"

    result = await db.execute(
        select(User).where(User.apple_user_id == guest_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            apple_user_id=guest_id,
            username=username,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        has_profile=user.has_profile
    )


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Logout user and revoke all their refresh tokens.

    This invalidates all sessions for the user, requiring re-authentication.
    """
    # Delete all refresh tokens for this user
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    await db.commit()

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("30/minute")
async def refresh_token_endpoint(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh_token.

    iOS should call this when access_token expires (401 error).
    Implements refresh token rotation for enhanced security.
    """
    try:
        # Verify refresh token is valid and has correct type
        payload = decode_refresh_token(refresh_request.refresh_token)
        user_id = int(payload.get("sub"))

        # Check if refresh token exists in database and isn't expired
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_request.refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        refresh_token_obj = result.scalar_one_or_none()

        if not refresh_token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Get user and verify they're still active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            # Revoke all tokens for inactive user
            await db.execute(
                delete(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )

        # Create new access token
        access_token = create_access_token({"sub": str(user.id)})

        # Rotate refresh token: create new one, delete old one
        new_refresh_token = create_refresh_token({"sub": str(user.id)})
        new_refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        # Delete old refresh token and add new one
        await db.delete(refresh_token_obj)
        db.add(new_refresh_token_obj)
        await db.commit()

        return AuthResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,  # Return rotated refresh token
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            has_profile=user.has_profile
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )
