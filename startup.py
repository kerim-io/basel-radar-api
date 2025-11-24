"""
Startup script for Railway deployment
Handles:
- Apple Sign-In private key decoding from base64 env var
- Directory creation
- APScheduler setup for background cleanup job
- Uvicorn server launch
"""

import os
import sys
import base64
import asyncio
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        "uploads",
        "uploads/profile_pictures",
        "keys"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ready: {directory}")


def setup_apple_private_key():
    """
    Decode Apple Sign-In private key from base64 environment variable
    and write to keys/5Y3L2S8R8R.p8
    """
    apple_key_base64 = os.getenv("APPLE_PRIVATE_KEY_BASE64")

    if not apple_key_base64:
        print("⚠️  WARNING: APPLE_PRIVATE_KEY_BASE64 not found in environment")
        print("⚠️  Apple Sign-In authentication will not work!")
        return False

    try:
        # Decode base64 to bytes
        key_content = base64.b64decode(apple_key_base64)

        # Write to file
        key_path = Path("keys/5Y3L2S8R8R.p8")
        key_path.write_bytes(key_content)

        # Set proper permissions (read-only for owner)
        os.chmod(key_path, 0o400)

        print(f"✓ Apple private key decoded and saved to {key_path}")
        return True

    except Exception as e:
        print(f"❌ Error decoding Apple private key: {e}")
        return False


def start_cleanup_scheduler():
    """
    Start APScheduler for background location cleanup job
    Runs every 5 minutes to remove expired anonymous locations
    """
    from services.location_cleanup import cleanup_expired_locations

    scheduler = AsyncIOScheduler()

    # Schedule cleanup job every 5 minutes
    scheduler.add_job(
        cleanup_expired_locations,
        trigger=IntervalTrigger(minutes=5),
        id='location_cleanup',
        name='Cleanup expired anonymous locations',
        replace_existing=True
    )

    scheduler.start()
    print("✓ Background cleanup scheduler started (runs every 5 minutes)")

    return scheduler


def main():
    """Main startup sequence"""
    print("=" * 60)
    print("🚀 BitBasel Backend - Railway Deployment Startup")
    print("=" * 60)

    # Step 1: Create directories
    print("\n[1/4] Setting up directories...")
    setup_directories()

    # Step 2: Decode Apple private key
    print("\n[2/4] Setting up Apple Sign-In private key...")
    apple_key_success = setup_apple_private_key()

    # Step 3: Start background scheduler
    print("\n[3/4] Starting background cleanup scheduler...")
    scheduler = start_cleanup_scheduler()

    # Step 4: Launch uvicorn
    print("\n[4/4] Starting uvicorn server...")
    print("=" * 60)

    # Get port from environment (Railway provides this)
    port = int(os.getenv("PORT", "8000"))

    # Import and run uvicorn
    import uvicorn

    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        scheduler.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
