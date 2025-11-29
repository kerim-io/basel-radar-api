#!/usr/bin/env python3
"""
Test script to trigger a follow notification.
User 9 (kimberly809) follows User 23 (aceeee).
"""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
import jwt
from core.config import settings


def generate_test_token(user_id: int) -> str:
    """Generate a valid JWT for testing"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def main():
    import httpx

    # User 9 (kimberly809) will follow User 23 (aceeee)
    follower_id = 9
    target_id = 23

    token = generate_test_token(follower_id)

    async with httpx.AsyncClient() as client:
        # First, delete existing follow if any (to make test repeatable)
        print(f"Attempting to unfollow user {target_id} first (cleanup)...")
        resp = await client.delete(
            f"http://localhost:8000/users/follow/{target_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Unfollow response: {resp.status_code}")

        # Now follow
        print(f"\nUser {follower_id} (kimberly809) following User {target_id} (aceeee)...")
        resp = await client.post(
            f"http://localhost:8000/users/follow/{target_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Follow response: {resp.status_code} - {resp.json()}")

        if resp.status_code == 200:
            print("\n✅ Follow created! Check server logs for notification.")
            print("   If user 23 is connected via WebSocket, they should see the notification.")
        else:
            print(f"\n❌ Follow failed: {resp.text}")


if __name__ == "__main__":
    asyncio.run(main())
