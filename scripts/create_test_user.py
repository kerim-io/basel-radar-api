"""
Create a second test user for testing multi-user features like follows
"""
import asyncio
from sqlalchemy import select
from db.database import create_async_session
from db.models import User
from services.auth_service import create_access_token, create_refresh_token
from datetime import datetime

async def create_test_user():
    db = create_async_session()

    try:
        # Create second test user
        test_apple_id = "test_user_streaming_001"

        # Check if user already exists
        result = await db.execute(
            select(User).where(User.apple_user_id == test_apple_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Test user already exists!")
            user = existing_user
        else:
            user = User(
                apple_user_id=test_apple_id,
                username="streamer_test",
                first_name="Test",
                last_name="Streamer",
                nickname="TestStreamer",
                email="streamer@test.com",
                bio="Test user for testing",
                can_post=True,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"✅ Created new test user!")

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        print("\n" + "="*60)
        print("🎥 TEST USER CREDENTIALS")
        print("="*60)
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Apple User ID: {user.apple_user_id}")
        print(f"\n🔑 Access Token:")
        print(f"{access_token}")
        print(f"\n🔄 Refresh Token:")
        print(f"{refresh_token}")
        print("="*60)
        print("\n💡 Usage:")
        print(f"  curl -H 'Authorization: Bearer {access_token}' \\")
        print(f"       http://localhost:8000/api/users/me")
        print("\n")

        return {
            "user_id": user.id,
            "username": user.username,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
