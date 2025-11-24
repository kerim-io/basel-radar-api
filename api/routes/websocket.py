from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict
import json
from datetime import datetime

from db.database import create_async_session
from db.models import Post, User, Livestream
from services.auth_service import decode_token

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        dead_connections = []
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append((user_id, connection))

        # Clean up dead connections
        for user_id, connection in dead_connections:
            self.disconnect(connection, user_id)


manager = ConnectionManager()


async def broadcast_location_update(location_id: str, latitude: float, longitude: float, area_name: str | None = None):
    """
    Broadcast anonymous location update to all connected clients

    Called when a user updates their location to notify map viewers in real-time.
    """
    await manager.broadcast({
        "type": "location_update",
        "location_id": location_id,
        "latitude": latitude,
        "longitude": longitude,
        "area_name": area_name,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_location_expired(location_id: str):
    """
    Broadcast that a location has expired (15 min timeout)

    Tells clients to remove the marker from the map.
    """
    await manager.broadcast({
        "type": "location_expired",
        "location_id": location_id,
        "timestamp": datetime.utcnow().isoformat()
    })


@router.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time feed updates
    Connect with: ws://localhost:8001/ws/feed?token={jwt}
    """
    db = None
    user_id = None

    try:
        # Verify token
        payload = decode_token(token)
        user_id = int(payload.get("sub"))

        # Get user
        db = create_async_session()
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await websocket.close(code=1008, reason="User not found")
            return

        # Accept connection
        await manager.connect(websocket, user_id)

        # Send initial feed
        result = await db.execute(
            select(Post, User)
            .join(User, Post.user_id == User.id)
            .order_by(desc(Post.created_at))
            .limit(50)
        )
        posts_data = result.all()

        initial_feed = [
            {
                "id": post.id,
                "user_id": post.user_id,
                "username": user.username,
                "content": post.content,
                "timestamp": post.created_at.isoformat(),
                "profile_pic_url": user.profile_picture,
                "media_url": post.media_url,
                "media_type": post.media_type,
                "latitude": post.latitude,
                "longitude": post.longitude,
                "likes_count": 0,
                "is_liked_by_current_user": False
            }
            for post, user in posts_data
        ]

        await websocket.send_json({
            "type": "initial_feed",
            "posts": initial_feed
        })

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            print(f"📨 WebSocket received message: {data}")

            # Handle new post
            if data.get("type") == "new_post":
                content = data.get("content")
                if content:
                    # Create post
                    new_post = Post(
                        user_id=user_id,
                        content=content,
                        media_url=data.get("media_url"),
                        media_type=data.get("media_type"),
                        latitude=data.get("latitude"),
                        longitude=data.get("longitude")
                    )
                    db.add(new_post)
                    await db.commit()
                    await db.refresh(new_post)

                    # Get user for response
                    result = await db.execute(select(User).where(User.id == user_id))
                    post_user = result.scalar_one()

                    # Broadcast to all clients
                    post_data = {
                        "type": "new_post",
                        "post": {
                            "id": new_post.id,
                            "user_id": new_post.user_id,
                            "username": post_user.username,
                            "content": new_post.content,
                            "timestamp": new_post.created_at.isoformat(),
                            "profile_pic_url": post_user.profile_picture,
                            "media_url": new_post.media_url,
                            "media_type": new_post.media_type,
                            "latitude": new_post.latitude,
                            "longitude": new_post.longitude,
                            "likes_count": 0,
                            "is_liked_by_current_user": False
                        }
                    }
                    await manager.broadcast(post_data)

    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if user_id:
            manager.disconnect(websocket, user_id)
        await websocket.close(code=1011, reason=str(e))
    finally:
        if db:
            await db.close()


@router.websocket("/ws/livestream/{room_id}")
async def livestream_tracking_websocket(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint to track livestream connection status.
    When the connection drops, automatically end the livestream in the database.
    """
    await websocket.accept()

    db = create_async_session()
    try:
        # Send confirmation
        await websocket.send_json({"type": "connected", "room_id": room_id})

        # Keep connection alive and wait for disconnect
        while True:
            try:
                # Receive heartbeat or status messages
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle viewer count updates
                if message.get("type") == "viewer_update":
                    viewer_count = message.get("count", 0)

                    result = await db.execute(
                        select(Livestream).where(
                            Livestream.room_id == room_id,
                            Livestream.status == 'active'
                        )
                    )
                    livestream = result.scalar_one_or_none()

                    if livestream:
                        if viewer_count > livestream.max_viewers:
                            livestream.max_viewers = viewer_count
                        await db.commit()

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"WebSocket error for room {room_id}: {e}")

    finally:
        # Connection dropped - end the livestream
        try:
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
                print(f"🔌 WebSocket disconnected - Livestream ended: room={room_id}, duration={duration}s")

        except Exception as e:
            print(f"Error ending livestream on disconnect: {e}")
        finally:
            await db.close()
