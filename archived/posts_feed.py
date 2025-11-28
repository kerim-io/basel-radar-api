"""
ARCHIVED: Posts Feed Endpoints
==============================
This file contains the feed-related REST endpoints that were removed
because the client app is no longer using a live feed.

Original location: api/routes/posts.py
Archived on: 2025-11-27

To restore: Copy these endpoints back to posts.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from db.database import get_async_session
from db.models import Post, User, Like
from api.dependencies import get_current_user


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
    venue_name: Optional[str] = None
    venue_id: Optional[str] = None
    likes_count: int = 0
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True


# To use these archived endpoints, add the following to your router:
# router = APIRouter(prefix="/posts", tags=["posts"])

async def get_feed(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> List[PostResponse]:
    """
    Get feed of posts with likes (optimized single query)

    ARCHIVED - No longer in use
    """
    # Optimized single query with aggregations and conditional logic
    stmt = (
        select(
            Post,
            User,
            func.count(Like.id).label('likes_count'),
            func.max(case((Like.user_id == current_user.id, 1), else_=0)).label('is_liked')
        )
        .join(User, Post.user_id == User.id)
        .outerjoin(Like, Post.id == Like.post_id)
        .group_by(Post.id, User.id)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=user.nickname,
            content=post.content,
            timestamp=post.created_at,
            profile_pic_url=user.profile_picture,
            media_url=post.media_url,
            media_type=post.media_type,
            latitude=post.latitude,
            longitude=post.longitude,
            venue_name=post.venue_name,
            venue_id=post.venue_id,
            likes_count=likes_count or 0,
            is_liked_by_current_user=bool(is_liked)
        )
        for post, user, likes_count, is_liked in rows
    ]


async def get_posts_by_time(
    date: str,  # YYYY-MM-DD
    hour: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> List[PostResponse]:
    """
    Get posts by specific date/hour for timeline scrubbing (optimized single query)

    ARCHIVED - No longer in use
    """
    # Validate date format
    try:
        target_date = datetime.fromisoformat(date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected YYYY-MM-DD"
        )

    # Validate hour if provided
    if hour is not None:
        if not isinstance(hour, int) or not (0 <= hour <= 23):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hour must be an integer between 0 and 23"
            )

    if hour is not None:
        start_time = target_date.replace(hour=hour, minute=0, second=0)
        end_time = start_time + timedelta(hours=1)
    else:
        start_time = target_date.replace(hour=0, minute=0, second=0)
        end_time = start_time + timedelta(days=1)

    # Optimized single query with aggregations
    stmt = (
        select(
            Post,
            User,
            func.count(Like.id).label('likes_count'),
            func.max(case((Like.user_id == current_user.id, 1), else_=0)).label('is_liked')
        )
        .join(User, Post.user_id == User.id)
        .outerjoin(Like, Post.id == Like.post_id)
        .where(Post.created_at >= start_time)
        .where(Post.created_at < end_time)
        .group_by(Post.id, User.id)
        .order_by(desc(Post.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=user.nickname,
            content=post.content,
            timestamp=post.created_at,
            profile_pic_url=user.profile_picture,
            media_url=post.media_url,
            media_type=post.media_type,
            latitude=post.latitude,
            longitude=post.longitude,
            venue_name=post.venue_name,
            venue_id=post.venue_id,
            likes_count=likes_count or 0,
            is_liked_by_current_user=bool(is_liked)
        )
        for post, user, likes_count, is_liked in rows
    ]
