"""
Drop and rebuild ALL tables in Railway PostgreSQL.

⚠️ WARNING: This script DELETES ALL DATA! Use with caution.

This script:
1. Drops ALL tables in the correct order (respecting foreign keys)
2. Recreates all tables from SQLAlchemy models
3. Runs migrations

Usage:
    DATABASE_URL="postgresql+asyncpg://..." python scripts/rebuild_railway_db.py

Or with Railway CLI:
    railway run python scripts/rebuild_railway_db.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from db.database import get_engine, Base, run_migrations


# All tables in dependency order (children first, parents last)
TABLES_TO_DROP = [
    # Junction/child tables first
    "google_pics",
    "bounce_attendees",
    "bounce_invites",
    "likes",
    "refresh_tokens",
    "check_ins",
    "livestreams",
    "posts",
    "bounces",
    "follows",
    # Parent tables last
    "places",
    "anonymous_locations",
    "users",
]


async def drop_all_tables():
    """Drop all tables in the correct order"""
    engine = get_engine()

    async with engine.begin() as conn:
        # First, drop all tables
        for table in TABLES_TO_DROP:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"   ✓ Dropped {table}")
            except Exception as e:
                print(f"   ✗ Failed to drop {table}: {e}")

        # Also drop any sequences
        print("\n📋 Dropping sequences...")
        result = await conn.execute(text("""
            SELECT sequence_name FROM information_schema.sequences
            WHERE sequence_schema = 'public'
        """))
        sequences = result.fetchall()
        for (seq_name,) in sequences:
            try:
                await conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq_name} CASCADE"))
                print(f"   ✓ Dropped sequence {seq_name}")
            except Exception as e:
                print(f"   ✗ Failed to drop sequence {seq_name}: {e}")


async def create_all_tables():
    """Create all tables from SQLAlchemy models"""
    # Import all models to ensure they're registered with Base
    from db import models  # noqa: F401

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("   ✓ All tables created from models")


async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in the environment.")
        sys.exit(1)

    print(f"🔗 DATABASE_URL detected.")
    print(f"   → {db_url[:50]}...\n")

    # Safety confirmation
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("    Tables to drop:", ", ".join(TABLES_TO_DROP))
    confirm = input("\n    Type 'YES' to confirm: ")

    if confirm != "YES":
        print("\n❌ Aborted.")
        sys.exit(1)

    try:
        print("\n🗑️  Dropping all tables...")
        await drop_all_tables()

        print("\n🔨 Creating all tables from models...")
        await create_all_tables()

        print("\n🔄 Running migrations...")
        await run_migrations()
        print("   ✓ Migrations complete")

        print("\n✅ Database rebuilt successfully!")

    except Exception as exc:
        print(f"\n❌ Error during rebuild: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
