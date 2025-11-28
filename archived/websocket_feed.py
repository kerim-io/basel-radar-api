"""
ARCHIVED: WebSocket Feed Endpoint
================================
This file contains the real-time feed WebSocket functionality that was removed
because the client app is no longer using a live feed.

Original location: api/routes/websocket.py
Archived on: 2025-11-27

To restore: Copy the websocket_feed function and related code back to websocket.py
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case
from typing import List, Dict
import json
import logging
from datetime import datetime, timezone

from db.database import create_async_session
from db.models import Post, User, Like
from services.auth_service import decode_token
from services.activity_clustering import get_activity_clusters

logger = logging.getLogger(__name__)


class FeedConnectionManager:
    """Connection manager for real-time feed WebSocket connections"""
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


feed_manager = FeedConnectionManager()


async def broadcast_activity_clusters(clusters: list):
    """
    Broadcast updated activity clusters to all connected clients.

    Called when a new post with location is created, to update map hotspots.
    Clusters show anonymized counts like "3 people here".
    """
    await feed_manager.broadcast({
        "type": "activity_clusters",
        "clusters": clusters,
        "timestamp": datetime.utcnow().isoformat()
    })


# To use this archived endpoint, add the following to your router:
# router = APIRouter(tags=["websocket"])

async def websocket_feed(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time feed updates
    Connect with: ws://localhost:8001/ws/feed?token={jwt}

    ARCHIVED - No longer in use
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
        await feed_manager.connect(websocket, user_id)

        # Send initial feed with optimized query
        # Single optimized query with aggregations
        result = await db.execute(
            select(
                Post,
                User,
                func.count(Like.id).label('likes_count'),
                func.max(case((Like.user_id == user_id, 1), else_=0)).label('is_liked')
            )
            .join(User, Post.user_id == User.id)
            .outerjoin(Like, Post.id == Like.post_id)
            .group_by(Post.id, User.id)
            .order_by(desc(Post.created_at))
            .limit(50)
        )
        posts_data = result.all()

        # Build initial feed
        initial_feed = []
        for post, user, likes_count, is_liked in posts_data:
            initial_feed.append({
                "id": post.id,
                "user_id": post.user_id,
                "username": user.nickname,
                "content": post.content,
                "timestamp": post.created_at.isoformat(),
                "profile_pic_url": user.profile_picture,
                "media_url": post.media_url,
                "media_type": post.media_type,
                "latitude": post.latitude,
                "longitude": post.longitude,
                "venue_name": post.venue_name,
                "venue_id": post.venue_id,
                "likes_count": likes_count or 0,
                "is_liked_by_current_user": bool(is_liked)
            })

        await websocket.send_json({
            "type": "initial_feed",
            "posts": initial_feed
        })

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                # Client disconnected normally - propagate to outer handler
                raise
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON received in WebSocket", extra={"user_id": user_id, "error": str(e)})
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            except Exception as e:
                logger.error("Error receiving WebSocket message", exc_info=True, extra={"user_id": user_id})
                break

            logger.debug("WebSocket received message", extra={"data": data, "user_id": user_id})

            # Validate message structure
            if not isinstance(data, dict):
                logger.warning("WebSocket message is not a dictionary", extra={"user_id": user_id})
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format: expected object"
                })
                continue

            message_type = data.get("type")
            if not message_type:
                logger.warning("WebSocket message missing type field", extra={"user_id": user_id})
                await websocket.send_json({
                    "type": "error",
                    "message": "Message must include 'type' field"
                })
                continue

            # Handle new post
            if message_type == "new_post":
                try:
                    content = data.get("content", "").strip()
                    media_url = data.get("media_url")

                    # Validate content - allow empty if media is present
                    if not content and not media_url:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Post must have content or media"
                        })
                        continue

                    # Validate content length (max 2000 chars)
                    if content and len(content) > 2000:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Post content exceeds maximum length of 2000 characters"
                        })
                        continue

                    # Validate coordinates if provided
                    latitude = data.get("latitude")
                    longitude = data.get("longitude")
                    if latitude is not None and longitude is not None:
                        try:
                            latitude = float(latitude)
                            longitude = float(longitude)
                            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                                raise ValueError("Coordinates out of range")
                        except (TypeError, ValueError) as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Invalid latitude/longitude values"
                            })
                            continue

                    # Extract venue fields
                    venue_name = data.get("venue_name")
                    venue_id = data.get("venue_id")

                    # Create post
                    new_post = Post(
                        user_id=user_id,
                        content=content,
                        media_url=data.get("media_url"),
                        media_type=data.get("media_type"),
                        latitude=latitude,
                        longitude=longitude,
                        venue_name=venue_name,
                        venue_id=venue_id
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
                            "username": post_user.nickname,
                            "content": new_post.content,
                            "timestamp": new_post.created_at.isoformat(),
                            "profile_pic_url": post_user.profile_picture,
                            "media_url": new_post.media_url,
                            "media_type": new_post.media_type,
                            "latitude": new_post.latitude,
                            "longitude": new_post.longitude,
                            "venue_name": new_post.venue_name,
                            "venue_id": new_post.venue_id,
                            "likes_count": 0,
                            "is_liked_by_current_user": False
                        }
                    }
                    await feed_manager.broadcast(post_data)

                    # Broadcast updated activity clusters if post has location
                    if new_post.latitude is not None and new_post.longitude is not None:
                        try:
                            clusters = await get_activity_clusters(db)
                            cluster_data = [
                                {
                                    "cluster_id": c.cluster_id,
                                    "latitude": c.latitude,
                                    "longitude": c.longitude,
                                    "count": c.count,
                                    "venue_name": c.venue_name,
                                    "last_activity": c.last_activity.isoformat()
                                }
                                for c in clusters
                            ]
                            await broadcast_activity_clusters(cluster_data)
                        except Exception as cluster_err:
                            logger.warning("Failed to broadcast activity clusters", extra={"error": str(cluster_err)})
                except Exception as e:
                    logger.error("Error creating post via WebSocket", exc_info=True, extra={"user_id": user_id})
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to create post"
                    })
            else:
                # Unknown message type
                logger.debug("Unknown WebSocket message type", extra={"user_id": user_id, "type": message_type})
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        if user_id:
            feed_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("WebSocket error", exc_info=True, extra={"user_id": user_id, "error": str(e)})
        if user_id:
            feed_manager.disconnect(websocket, user_id)
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        if db:
            await db.close()
