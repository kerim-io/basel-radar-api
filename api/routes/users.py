from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import aiofiles
from pathlib import Path
import uuid

from db.database import get_async_session
from db.models import User, Follow
from api.dependencies import get_current_user
from core.config import settings

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    employer: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    nickname: Optional[str]
    employer: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    profile_picture: Optional[str]
    has_profile: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    bio: Optional[str]
    profile_picture: Optional[str]
    email: Optional[str]

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.get("/me/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user full profile"""
    return ProfileResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        nickname=current_user.nickname,
        employer=current_user.employer,
        phone=current_user.phone,
        email=current_user.email,
        profile_picture=current_user.profile_picture,
        has_profile=current_user.has_profile
    )


@router.put("/me/profile", response_model=ProfileResponse)
async def update_profile_full(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update current user profile (Saatchi aesthetic)"""
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.employer is not None:
        current_user.employer = profile_data.employer
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.email is not None:
        current_user.email = profile_data.email
    if profile_data.profile_picture_url is not None:
        current_user.profile_picture = profile_data.profile_picture_url

    await db.commit()
    await db.refresh(current_user)

    return ProfileResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        nickname=current_user.nickname,
        employer=current_user.employer,
        phone=current_user.phone,
        email=current_user.email,
        profile_picture=current_user.profile_picture,
        has_profile=current_user.has_profile
    )


@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Upload profile picture (multipart/form-data)"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, WEBP allowed")

    # Generate unique filename
    ext = file.filename.split(".")[-1]
    filename = f"profile_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"

    # Save to uploads directory
    upload_dir = Path(settings.UPLOAD_DIR) / "profile_pictures"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Update user profile picture URL
    profile_picture_url = f"/files/profile_pictures/{filename}"
    current_user.profile_picture = profile_picture_url
    await db.commit()

    return {
        "success": True,
        "profile_picture_url": profile_picture_url
    }


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update current user profile (legacy)"""
    if update_data.username:
        current_user.username = update_data.username
    if update_data.bio:
        current_user.bio = update_data.bio
    if update_data.profile_picture:
        current_user.profile_picture = update_data.profile_picture

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/follow/{user_id}")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Follow a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Check if already following
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Already following")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    await db.commit()

    return {"status": "success"}


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Unfollow a user"""
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    follow = result.scalar_one_or_none()

    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    await db.delete(follow)
    await db.commit()

    return {"status": "success"}
