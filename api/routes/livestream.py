from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
from db.database import get_async_session
from db.models import User, Livestream
from services.auth_service import decode_token
from pydantic import BaseModel
import aiohttp
import os

router = APIRouter(prefix="/livestream", tags=["livestream"])

MEDIA_SERVER_URL = os.getenv("MEDIA_SERVER_URL", "http://localhost:9001")


class LiveUserResponse(BaseModel):
    id: int
    user_id: int
    username: str
    room_id: str
    profile_pic_url: str | None

    class Config:
        from_attributes = True


@router.get("/active", response_model=List[LiveUserResponse])
async def get_active_livestreams(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all currently active livestreams from any user (not just followed users).
    """
    try:
        # Call the media server to get active rooms
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{MEDIA_SERVER_URL}/stats") as resp:
                if resp.status != 200:
                    return []

                stats = await resp.json()
                active_rooms = stats.get("rooms", [])

                if not active_rooms:
                    return []

                # Get user info for each active room
                live_users = []
                for room in active_rooms:
                    room_id = room.get("room_id")
                    host_id = room.get("host_id")

                    if not host_id:
                        continue

                    # Get user from database
                    result = await db.execute(select(User).where(User.id == host_id))
                    user = result.scalar_one_or_none()

                    if user:
                        live_users.append(LiveUserResponse(
                            id=user.id,
                            user_id=user.id,
                            username=user.nickname or user.username or user.email or f"user_{user.id}",
                            room_id=room_id,
                            profile_pic_url=user.profile_picture
                        ))

                return live_users
    except Exception as e:
        print(f"Error fetching active livestreams: {e}")
        return []


class StartStreamResponse(BaseModel):
    room_id: str
    websocket_url: str


@router.post("/start", response_model=StartStreamResponse)
async def start_livestream(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Start a new livestream. Creates a room on the media server.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]

    try:
        user_id = decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "post_id": f"post_{user_id}",
                "host_user_id": str(user_id)
            }

            async with session.post(
                f"{MEDIA_SERVER_URL}/room/create",
                headers={"Authorization": authorization},
                json=payload
            ) as resp:
                if resp.status != 201:
                    text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=f"Media server error: {text}")

                data = await resp.json()
                room_id = data.get("room_id")

                if not room_id:
                    raise HTTPException(status_code=500, detail="No room_id returned from media server")

                # Save livestream to database
                livestream = Livestream(
                    user_id=user_id,
                    room_id=room_id,
                    post_id=f"post_{user_id}",
                    status='active'
                )
                db.add(livestream)
                await db.commit()
                await db.refresh(livestream)

                print(f"📹 Livestream started: user={user_id}, room={room_id}, db_id={livestream.id}")

                websocket_url = f"ws://localhost:9001/room/{room_id}/host"

                return StartStreamResponse(
                    room_id=room_id,
                    websocket_url=websocket_url
                )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to media server: {str(e)}")
    except Exception as e:
        print(f"Error starting livestream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class StopStreamResponse(BaseModel):
    status: str
    room_id: str


@router.post("/stop/{room_id}", response_model=StopStreamResponse)
async def stop_livestream(
    room_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Stop an active livestream.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]

    try:
        user_id = decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    try:
        # Update livestream in database
        result = await db.execute(
            select(Livestream).where(
                Livestream.room_id == room_id,
                Livestream.status == 'active'
            )
        )
        livestream = result.scalar_one_or_none()

        if livestream:
            livestream.ended_at = datetime.utcnow()
            livestream.status = 'ended'
            await db.commit()

            duration = livestream.duration_seconds
            print(f"🛑 Livestream ended: room={room_id}, duration={duration}s, max_viewers={livestream.max_viewers}")

        # Stop room on media server
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{MEDIA_SERVER_URL}/room/{room_id}/stop",
                headers={"Authorization": authorization}
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=f"Media server error: {text}")

                return StopStreamResponse(
                    status="stopped",
                    room_id=room_id
                )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to media server: {str(e)}")
    except Exception as e:
        print(f"Error stopping livestream: {e}")
        raise HTTPException(status_code=500, detail=str(e))
