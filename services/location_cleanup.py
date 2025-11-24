"""Background cleanup job for expired anonymous locations"""

import asyncio
from datetime import datetime, timedelta, UTC

from sqlalchemy import select, delete

from db.database import create_async_session
from db.models import AnonymousLocation
from api.routes.websocket import broadcast_location_expired


async def cleanup_expired_locations():
    """
    Remove anonymous locations older than 15 minutes and broadcast expiration

    This job should be run periodically (every 5 minutes recommended)
    """
    db = create_async_session()

    try:
        expiration_threshold = datetime.now(UTC) - timedelta(minutes=15)

        # Get expired location IDs before deleting
        result = await db.execute(
            select(AnonymousLocation.location_id)
            .where(AnonymousLocation.last_updated < expiration_threshold)
        )
        expired_ids = [str(row[0]) for row in result.all()]

        # Delete expired locations
        delete_result = await db.execute(
            delete(AnonymousLocation)
            .where(AnonymousLocation.last_updated < expiration_threshold)
        )
        await db.commit()

        deleted_count = delete_result.rowcount

        # Broadcast expiration to connected clients
        for location_id in expired_ids:
            await broadcast_location_expired(location_id)

        print(f"🧹 Cleanup: Removed {deleted_count} expired locations")

        return deleted_count

    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        await db.rollback()
        return 0
    finally:
        await db.close()


async def run_cleanup_loop(interval_seconds: int = 300):
    """
    Run cleanup job in an infinite loop

    Args:
        interval_seconds: How often to run cleanup (default 5 minutes = 300 seconds)
    """
    print(f"🚀 Starting location cleanup job (every {interval_seconds}s)")

    while True:
        try:
            await cleanup_expired_locations()
        except Exception as e:
            print(f"❌ Cleanup loop error: {e}")

        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    # For standalone execution
    asyncio.run(run_cleanup_loop())
