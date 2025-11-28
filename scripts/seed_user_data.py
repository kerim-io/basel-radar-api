#!/usr/bin/env python3
"""
Seed data for a specific user:
- Followers and following relationships
- Bounces around Miami with invites
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy import text
from db.database import create_async_session

fake = Faker()

# Target user's Apple ID
TARGET_APPLE_ID = "000300.c99203e0ac804503b08fa8e710532e3f.2006"

# Miami venues for bounces
MIAMI_VENUES = [
    {"name": "LIV Miami", "address": "4441 Collins Ave, Miami Beach, FL 33140", "lat": 25.8167, "lon": -80.1228},
    {"name": "Basement Miami", "address": "2901 Collins Ave, Miami Beach, FL 33140", "lat": 25.8023, "lon": -80.1277},
    {"name": "Story Nightclub", "address": "136 Collins Ave, Miami Beach, FL 33139", "lat": 25.7755, "lon": -80.1341},
    {"name": "E11EVEN Miami", "address": "29 NE 11th St, Miami, FL 33132", "lat": 25.7863, "lon": -80.1918},
    {"name": "Wynwood Walls", "address": "2520 NW 2nd Ave, Miami, FL 33127", "lat": 25.8012, "lon": -80.1992},
    {"name": "Faena Hotel Terrace", "address": "3201 Collins Ave, Miami Beach, FL 33140", "lat": 25.8194, "lon": -80.1225},
    {"name": "Soho Beach House Rooftop", "address": "4385 Collins Ave, Miami Beach, FL 33140", "lat": 25.8154, "lon": -80.1229},
    {"name": "The Surf Club Restaurant", "address": "9011 Collins Ave, Surfside, FL 33154", "lat": 25.8788, "lon": -80.1204},
    {"name": "Swan Miami", "address": "90 NE 39th St, Miami, FL 33137", "lat": 25.8118, "lon": -80.1928},
    {"name": "Carbone Miami", "address": "49 Collins Ave, Miami Beach, FL 33139", "lat": 25.7740, "lon": -80.1345},
    {"name": "Joia Beach", "address": "1 Star Island Dr, Miami Beach, FL 33139", "lat": 25.7795, "lon": -80.1552},
    {"name": "The Broken Shaker", "address": "2727 Indian Creek Dr, Miami Beach, FL 33140", "lat": 25.8055, "lon": -80.1269},
    {"name": "Perez Art Museum", "address": "1103 Biscayne Blvd, Miami, FL 33132", "lat": 25.7857, "lon": -80.1866},
    {"name": "Casa Tua Miami Beach", "address": "1700 James Ave, Miami Beach, FL 33139", "lat": 25.7918, "lon": -80.1335},
    {"name": "Kiki on the River", "address": "450 NW North River Dr, Miami, FL 33128", "lat": 25.7781, "lon": -80.1997},
]

EMPLOYERS = [
    "Gagosian Gallery", "Pace Gallery", "David Zwirner", "Hauser & Wirth",
    "Christie's", "Sotheby's", "White Cube", "Perrotin", "Lehmann Maupin",
    "Google", "Apple", "Meta", "Netflix", "Spotify", "Goldman Sachs",
    "Morgan Stanley", "Art Collector", "Independent Curator", "Fashion Designer",
]


async def seed_user_data():
    """Add followers, following, and bounces for the target user"""
    db = create_async_session()

    try:
        print(f"Looking up user: {TARGET_APPLE_ID}")

        # Get target user
        result = await db.execute(
            text("SELECT id, nickname FROM users WHERE apple_user_id = :apple_id"),
            {"apple_id": TARGET_APPLE_ID}
        )
        row = result.fetchone()

        if not row:
            print(f"User not found! Creating user...")
            result = await db.execute(
                text("""
                    INSERT INTO users (
                        apple_user_id, first_name, last_name, nickname,
                        can_post, phone_visible, email_visible, is_active
                    ) VALUES (
                        :apple_id, 'Kerim', 'Test', 'kerim',
                        true, false, false, true
                    ) RETURNING id, nickname
                """),
                {"apple_id": TARGET_APPLE_ID}
            )
            row = result.fetchone()
            await db.commit()

        target_user_id = row[0]
        target_nickname = row[1]
        print(f"Target user: ID={target_user_id}, nickname={target_nickname}")

        # Create 20 new users to be followers/following
        print("\nCreating 20 new users...")
        new_user_ids = []

        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            nickname = f"{first_name.lower()}{random.randint(1, 999)}"

            result = await db.execute(
                text("""
                    INSERT INTO users (
                        apple_user_id, first_name, last_name, nickname,
                        employer, email, can_post, phone_visible, email_visible,
                        is_active, profile_picture
                    ) VALUES (
                        :apple_id, :first_name, :last_name, :nickname,
                        :employer, :email, true, false, false,
                        true, :profile_pic
                    ) RETURNING id
                """),
                {
                    "apple_id": f"seed_{fake.uuid4()}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "nickname": nickname,
                    "employer": random.choice(EMPLOYERS),
                    "email": fake.email(),
                    "profile_pic": f"https://i.pravatar.cc/150?u={nickname}",
                }
            )
            new_user_ids.append(result.scalar())
            print(f"   Created user: {first_name} {last_name} (@{nickname})")

        await db.commit()

        # Create followers (10 users follow the target)
        print(f"\nAdding 10 followers for user {target_user_id}...")
        follower_ids = random.sample(new_user_ids, 10)

        for follower_id in follower_ids:
            await db.execute(
                text("""
                    INSERT INTO follows (follower_id, following_id)
                    VALUES (:follower, :following)
                    ON CONFLICT DO NOTHING
                """),
                {"follower": follower_id, "following": target_user_id}
            )

        # Create following (target follows 12 users)
        print(f"Adding 12 users that {target_user_id} follows...")
        following_ids = random.sample(new_user_ids, 12)

        for following_id in following_ids:
            await db.execute(
                text("""
                    INSERT INTO follows (follower_id, following_id)
                    VALUES (:follower, :following)
                    ON CONFLICT DO NOTHING
                """),
                {"follower": target_user_id, "following": following_id}
            )

        await db.commit()
        print(f"   {len(follower_ids)} users now follow you")
        print(f"   You now follow {len(following_ids)} users")

        # Create bounces around Miami
        print("\nCreating bounces around Miami...")
        now = datetime.now(timezone.utc)
        bounces_created = []

        # 3 bounces happening now
        print("\n   NOW bounces:")
        for i in range(3):
            venue = MIAMI_VENUES[i]
            creator_id = random.choice(new_user_ids)

            result = await db.execute(
                text("""
                    INSERT INTO bounces (
                        creator_id, venue_name, venue_address,
                        latitude, longitude, bounce_time, is_now, is_public, status
                    ) VALUES (
                        :creator_id, :venue_name, :venue_address,
                        :lat, :lon, :bounce_time, true, :is_public, 'active'
                    ) RETURNING id
                """),
                {
                    "creator_id": creator_id,
                    "venue_name": venue["name"],
                    "venue_address": venue["address"],
                    "lat": venue["lat"],
                    "lon": venue["lon"],
                    "bounce_time": now,
                    "is_public": random.choice([True, False]),
                }
            )
            bounce_id = result.scalar()
            bounces_created.append({"id": bounce_id, "venue": venue["name"], "time": "NOW"})
            print(f"      - {venue['name']} (Bounce #{bounce_id})")

        # 5 bounces later today (1-8 hours from now)
        print("\n   Later today bounces:")
        for i in range(5):
            venue = MIAMI_VENUES[3 + i]
            creator_id = random.choice(new_user_ids)
            hours_later = random.randint(1, 8)
            bounce_time = now + timedelta(hours=hours_later)

            result = await db.execute(
                text("""
                    INSERT INTO bounces (
                        creator_id, venue_name, venue_address,
                        latitude, longitude, bounce_time, is_now, is_public, status
                    ) VALUES (
                        :creator_id, :venue_name, :venue_address,
                        :lat, :lon, :bounce_time, false, :is_public, 'active'
                    ) RETURNING id
                """),
                {
                    "creator_id": creator_id,
                    "venue_name": venue["name"],
                    "venue_address": venue["address"],
                    "lat": venue["lat"],
                    "lon": venue["lon"],
                    "bounce_time": bounce_time,
                    "is_public": random.choice([True, False]),
                }
            )
            bounce_id = result.scalar()
            time_str = bounce_time.strftime("%I:%M %p")
            bounces_created.append({"id": bounce_id, "venue": venue["name"], "time": time_str})
            print(f"      - {venue['name']} at {time_str} (Bounce #{bounce_id})")

        # 4 bounces tonight (8-12 hours from now)
        print("\n   Tonight bounces:")
        for i in range(4):
            venue = MIAMI_VENUES[8 + i]
            creator_id = random.choice(new_user_ids)
            hours_later = random.randint(8, 12)
            bounce_time = now + timedelta(hours=hours_later)

            result = await db.execute(
                text("""
                    INSERT INTO bounces (
                        creator_id, venue_name, venue_address,
                        latitude, longitude, bounce_time, is_now, is_public, status
                    ) VALUES (
                        :creator_id, :venue_name, :venue_address,
                        :lat, :lon, :bounce_time, false, :is_public, 'active'
                    ) RETURNING id
                """),
                {
                    "creator_id": creator_id,
                    "venue_name": venue["name"],
                    "venue_address": venue["address"],
                    "lat": venue["lat"],
                    "lon": venue["lon"],
                    "bounce_time": bounce_time,
                    "is_public": random.choice([True, False]),
                }
            )
            bounce_id = result.scalar()
            time_str = bounce_time.strftime("%I:%M %p")
            bounces_created.append({"id": bounce_id, "venue": venue["name"], "time": time_str})
            print(f"      - {venue['name']} at {time_str} (Bounce #{bounce_id})")

        await db.commit()

        # Invite target user to 5 bounces
        print(f"\nInviting you to 5 bounces...")
        invite_bounces = random.sample(bounces_created, 5)

        for bounce in invite_bounces:
            await db.execute(
                text("""
                    INSERT INTO bounce_invites (bounce_id, user_id)
                    VALUES (:bounce_id, :user_id)
                    ON CONFLICT DO NOTHING
                """),
                {"bounce_id": bounce["id"], "user_id": target_user_id}
            )
            print(f"   - Invited to: {bounce['venue']} ({bounce['time']})")

        await db.commit()

        # Summary
        print("\n" + "=" * 60)
        print("SEED COMPLETE!")
        print("=" * 60)
        print(f"Target User: {target_nickname} (ID: {target_user_id})")
        print(f"New users created: 20")
        print(f"Followers added: 10")
        print(f"Following added: 12")
        print(f"Bounces created: {len(bounces_created)}")
        print(f"Bounce invites for you: 5")
        print("=" * 60)

    except Exception as e:
        await db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed_user_data())
