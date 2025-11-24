from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from pathlib import Path

from db.database import get_async_session
from db.models import Post, User, Like
from api.dependencies import get_current_user
from core.config import settings

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an image and return the URL"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )

    # Validate file size (10MB max)
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )

    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Save file
    upload_path = Path(settings.UPLOAD_DIR) / unique_filename
    with open(upload_path, "wb") as f:
        f.write(contents)

    # Return URL
    file_url = f"/files/{unique_filename}"

    return {
        "url": file_url,
        "filename": unique_filename
    }


class PostCreate(BaseModel):
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PostResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    content: str
    timestamp: datetime
    profile_pic_url: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    likes_count: int = 0
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    likes_count: int
    is_liked: bool


@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new post (text only for MVP)"""
    post = Post(
        user_id=current_user.id,
        content=post_data.content,
        media_url=post_data.media_url,
        media_type=post_data.media_type,
        latitude=post_data.latitude,
        longitude=post_data.longitude
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        username=current_user.username,
        content=post.content,
        timestamp=post.created_at,
        profile_pic_url=current_user.profile_picture,
        media_url=post.media_url,
        media_type=post.media_type,
        latitude=post.latitude,
        longitude=post.longitude
    )


@router.get("/feed", response_model=List[PostResponse])
async def get_feed(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get feed of posts with likes"""
    result = await db.execute(
        select(Post, User)
        .join(User, Post.user_id == User.id)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    )

    posts_data = result.all()

    # Get likes for all posts in one query
    post_ids = [post.id for post, _ in posts_data]
    likes_result = await db.execute(
        select(Like.post_id, func.count(Like.id).label('count'))
        .where(Like.post_id.in_(post_ids))
        .group_by(Like.post_id)
    )
    likes_counts = dict(likes_result.all())

    # Get current user's likes
    user_likes_result = await db.execute(
        select(Like.post_id)
        .where(Like.user_id == current_user.id)
        .where(Like.post_id.in_(post_ids))
    )
    user_liked_posts = set(row[0] for row in user_likes_result.all())

    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=user.username,
            content=post.content,
            timestamp=post.created_at,
            profile_pic_url=user.profile_picture,
            media_url=post.media_url,
            media_type=post.media_type,
            latitude=post.latitude,
            longitude=post.longitude,
            likes_count=likes_counts.get(post.id, 0),
            is_liked_by_current_user=(post.id in user_liked_posts)
        )
        for post, user in posts_data
    ]


@router.get("/by-time", response_model=List[PostResponse])
async def get_posts_by_time(
    date: str,  # YYYY-MM-DD
    hour: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get posts by specific date/hour for timeline scrubbing"""
    from datetime import datetime, timedelta

    target_date = datetime.fromisoformat(date)

    if hour is not None:
        start_time = target_date.replace(hour=hour, minute=0, second=0)
        end_time = start_time + timedelta(hours=1)
    else:
        start_time = target_date.replace(hour=0, minute=0, second=0)
        end_time = start_time + timedelta(days=1)

    result = await db.execute(
        select(Post, User)
        .join(User, Post.user_id == User.id)
        .where(Post.created_at >= start_time)
        .where(Post.created_at < end_time)
        .order_by(desc(Post.created_at))
    )

    posts_data = result.all()

    # Get likes for all posts
    post_ids = [post.id for post, _ in posts_data]
    likes_result = await db.execute(
        select(Like.post_id, func.count(Like.id).label('count'))
        .where(Like.post_id.in_(post_ids))
        .group_by(Like.post_id)
    )
    likes_counts = dict(likes_result.all())

    # Get current user's likes
    user_likes_result = await db.execute(
        select(Like.post_id)
        .where(Like.user_id == current_user.id)
        .where(Like.post_id.in_(post_ids))
    )
    user_liked_posts = set(row[0] for row in user_likes_result.all())

    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=user.username,
            content=post.content,
            timestamp=post.created_at,
            profile_pic_url=user.profile_picture,
            media_url=post.media_url,
            media_type=post.media_type,
            latitude=post.latitude,
            longitude=post.longitude,
            likes_count=likes_counts.get(post.id, 0),
            is_liked_by_current_user=(post.id in user_liked_posts)
        )
        for post, user in posts_data
    ]
