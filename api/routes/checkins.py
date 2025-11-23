from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from db.database import get_async_session
from db.models import CheckIn, User
from api.dependencies import get_current_user
from services.geofence import is_in_basel_area

router = APIRouter(prefix="/checkins", tags=["checkins"])


class CheckInCreate(BaseModel):
    latitude: float
    longitude: float
    location_name: str


class CheckInResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    latitude: float
    longitude: float
    location_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=CheckInResponse)
async def create_checkin(
    checkin_data: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Check in at Art Basel location"""
    # Verify location is in Basel area
    if not is_in_basel_area(checkin_data.latitude, checkin_data.longitude):
        raise HTTPException(
            status_code=400,
            detail="Location must be within Art Basel Miami area"
        )

    checkin = CheckIn(
        user_id=current_user.id,
        latitude=checkin_data.latitude,
        longitude=checkin_data.longitude,
        location_name=checkin_data.location_name
    )
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)

    return CheckInResponse(
        id=checkin.id,
        user_id=checkin.user_id,
        username=current_user.username,
        latitude=checkin.latitude,
        longitude=checkin.longitude,
        location_name=checkin.location_name,
        created_at=checkin.created_at
    )


@router.get("/recent", response_model=List[CheckInResponse])
async def get_recent_checkins(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get recent check-ins"""
    result = await db.execute(
        select(CheckIn, User)
        .join(User, CheckIn.user_id == User.id)
        .order_by(desc(CheckIn.created_at))
        .limit(limit)
    )

    checkins_data = result.all()

    return [
        CheckInResponse(
            id=checkin.id,
            user_id=checkin.user_id,
            username=user.username,
            latitude=checkin.latitude,
            longitude=checkin.longitude,
            location_name=checkin.location_name,
            created_at=checkin.created_at
        )
        for checkin, user in checkins_data
    ]
