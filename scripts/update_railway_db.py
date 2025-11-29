"""
Sync Railway PostgreSQL schema with the local project schema.

This script connects to the DATABASE_URL (PostgreSQL) and runs the
SQLModel metadata create_all() operation using an async engine.

⚠️ Note:
This only creates missing tables / indexes.
It does NOT perform destructive ALTERs or modify existing columns.

Usage:
    export DATABASE_URL=postgresql+asyncpg://user:pass@host/db
    python scripts/sync_railway_schema.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import get_engine, create_db_and_tables  # You will implement these


async def main() -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in the environment.")
        sys.exit(1)

    print(f"🔗 DATABASE_URL detected.")
    print(f"   → {db_url}\n")

    try:
        engine = get_engine()
        print(f"🔌 Engine created (async). URL: {engine.url}\n")

        await create_db_and_tables()
        print("✅ Railway schema synchronized successfully!")

    except Exception as exc:
        print(f"\n❌ Error during sync: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
