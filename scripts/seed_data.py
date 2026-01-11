#!/usr/bin/env python3
"""
Seed the database with test data:
- 300 users
- ~1000-1500 posts with Miami locations
- ~2000-3000 follow relationships
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy import text

from db.database import create_async_session

fake = Faker()

# Miami area locations with names
MIAMI_LOCATIONS = [
    {"name": "Art Basel Convention Center", "lat": 25.7907, "lon": -80.1300},
    {"name": "Wynwood Walls", "lat": 25.8012, "lon": -80.1992},
    {"name": "South Beach", "lat": 25.7826, "lon": -80.1341},
    {"name": "Design District", "lat": 25.8131, "lon": -80.1926},
    {"name": "Pérez Art Museum Miami", "lat": 25.7857, "lon": -80.1866},
    {"name": "Faena Hotel Miami Beach", "lat": 25.8194, "lon": -80.1225},
    {"name": "Soho Beach House", "lat": 25.8154, "lon": -80.1229},
    {"name": "LIV Miami", "lat": 25.8167, "lon": -80.1228},
    {"name": "Rubell Museum", "lat": 25.8089, "lon": -80.2069},
    {"name": "Bass Museum of Art", "lat": 25.7963, "lon": -80.1308},
    {"name": "The Setai Miami Beach", "lat": 25.7943, "lon": -80.1287},
    {"name": "Fontainebleau Miami Beach", "lat": 25.8173, "lon": -80.1227},
    {"name": "Versace Mansion", "lat": 25.7812, "lon": -80.1305},
    {"name": "Bayside Marketplace", "lat": 25.7784, "lon": -80.1868},
    {"name": "Vizcaya Museum", "lat": 25.7445, "lon": -80.2106},
    {"name": "Little Havana", "lat": 25.7654, "lon": -80.2191},
    {"name": "Brickell City Centre", "lat": 25.7650, "lon": -80.1936},
    {"name": "Coconut Grove", "lat": 25.7270, "lon": -80.2416},
]

# Art-related post content templates
POST_TEMPLATES = [
    "Amazing installation at {location}! 🎨",
    "The energy here at {location} is incredible tonight",
    "Just saw the most mind-blowing piece at {location}",
    "Art Basel vibes at {location} ✨",
    "Can't believe what I'm seeing at {location}",
    "This is why I love Miami during Art Basel",
    "Found this gem at {location}",
    "The crowds at {location} are insane!",
    "Best art I've seen all week at {location}",
    "Late night at {location} 🌙",
    "Pre-party at {location}",
    "VIP access at {location} was worth it",
    "Meeting so many amazing artists at {location}",
    "The view from {location} is stunning",
    "Just ran into a celebrity at {location}! 👀",
    "After party at {location}",
    "Networking at {location}",
    "This piece at {location} speaks to me",
    "Incredible performance art at {location}",
    "The installations at {location} are next level",
]

EMPLOYERS = [
    "Google", "Apple", "Meta", "Amazon", "Netflix", "Spotify", "Airbnb",
    "Uber", "Lyft", "Twitter", "TikTok", "Snap Inc", "Pinterest",
    "Sotheby's", "Christie's", "Gagosian Gallery", "Pace Gallery",
    "David Zwirner", "Hauser & Wirth", "White Cube", "Perrotin",
    "Goldman Sachs", "Morgan Stanley", "JPMorgan", "Blackstone",
    "McKinsey", "BCG", "Bain", "Deloitte", "KPMG", "PwC",
    "Freelance Artist", "Independent Curator", "Art Consultant",
    "Museum Director", "Gallery Owner", "Art Collector",
    "Fashion Designer", "Architect", "Interior Designer",
]


def random_location():
    """Get a random Miami location with slight coordinate variation"""
    loc = random.choice(MIAMI_LOCATIONS)
    # Add small random offset (within ~100m)
    lat_offset = random.uniform(-0.001, 0.001)
    lon_offset = random.uniform(-0.001, 0.001)
    return {
        "name": loc["name"],
        "lat": loc["lat"] + lat_offset,
        "lon": loc["lon"] + lon_offset,
    }


def generate_post_content(location_name):
    """Generate realistic post content"""
    template = random.choice(POST_TEMPLATES)
    return template.format(location=location_name)


async def seed_database():
    """Main seeding function"""
    db = create_async_session()

    try:
        print("🌱 Starting database seed...")

        # Clear existing data
        print("Clearing existing data...")
        await db.execute(text("DELETE FROM bounce_invites"))
        await db.execute(text("DELETE FROM bounces"))
        await db.execute(text("DELETE FROM follows"))
        await db.execute(text("DELETE FROM refresh_tokens"))
        await db.execute(text("DELETE FROM anonymous_locations"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()

        # Create 300 users
        print("👥 Creating 300 users...")
        user_ids = []

        for i in range(300):
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
                        :employer, :email, :can_post, false, false,
                        true, :profile_pic
                    ) RETURNING id
                """),
                {
                    "apple_id": f"apple_{fake.uuid4()}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "nickname": nickname,
                    "employer": random.choice(EMPLOYERS) if random.random() > 0.3 else None,
                    "email": fake.email() if random.random() > 0.5 else None,
                    "can_post": random.random() > 0.1,  # 90% can post
                    "profile_pic": f"https://i.pravatar.cc/150?u={nickname}",
                }
            )
            user_id = result.scalar()
            user_ids.append(user_id)

            if (i + 1) % 50 == 0:
                print(f"   Created {i + 1} users...")

        await db.commit()
        print(f"✅ Created {len(user_ids)} users")

        # Create posts (3-7 per user)
        print("📝 Creating posts...")
        post_count = 0
        now = datetime.now(timezone.utc)

        for user_id in user_ids:
            num_posts = random.randint(3, 7)

            for _ in range(num_posts):
                loc = random_location()
                content = generate_post_content(loc["name"])

                # Random timestamp in last 5 days
                hours_ago = random.randint(0, 120)
                created_at = now - timedelta(hours=hours_ago)

                # 70% have location, 30% text only
                has_location = random.random() > 0.3

                await db.execute(
                    text("""
                        INSERT INTO posts (
                            user_id, content, latitude, longitude,
                            venue_name, created_at
                        ) VALUES (
                            :user_id, :content, :lat, :lon,
                            :venue_name, :created_at
                        )
                    """),
                    {
                        "user_id": user_id,
                        "content": content,
                        "lat": loc["lat"] if has_location else None,
                        "lon": loc["lon"] if has_location else None,
                        "venue_name": loc["name"] if has_location else None,
                        "created_at": created_at,
                    }
                )
                post_count += 1

            if post_count % 200 == 0:
                print(f"   Created {post_count} posts...")

        await db.commit()
        print(f"✅ Created {post_count} posts")

        # Create follows (average 10-20 per user)
        print("🔗 Creating follow relationships...")
        follow_count = 0

        for user_id in user_ids:
            # Each user follows 5-25 random other users
            num_follows = random.randint(5, 25)
            follows = random.sample([u for u in user_ids if u != user_id], min(num_follows, len(user_ids) - 1))

            for followed_id in follows:
                try:
                    await db.execute(
                        text("""
                            INSERT INTO follows (follower_id, following_id)
                            VALUES (:follower, :following)
                            ON CONFLICT DO NOTHING
                        """),
                        {"follower": user_id, "following": followed_id}
                    )
                    follow_count += 1
                except:
                    pass  # Skip duplicates

            if follow_count % 500 == 0:
                print(f"   Created {follow_count} follows...")

        await db.commit()
        print(f"✅ Created {follow_count} follow relationships")

        # Create some likes
        print("❤️  Creating likes...")
        like_count = 0

        # Get all post IDs
        result = await db.execute(text("SELECT id FROM posts"))
        post_ids = [row[0] for row in result.fetchall()]

        for user_id in user_ids:
            # Each user likes 10-50 random posts
            num_likes = random.randint(10, 50)
            liked_posts = random.sample(post_ids, min(num_likes, len(post_ids)))

            for post_id in liked_posts:
                try:
                    await db.execute(
                        text("""
                            INSERT INTO likes (user_id, post_id)
                            VALUES (:user_id, :post_id)
                            ON CONFLICT DO NOTHING
                        """),
                        {"user_id": user_id, "post_id": post_id}
                    )
                    like_count += 1
                except:
                    pass

        await db.commit()
        print(f"✅ Created {like_count} likes")

        # Summary
        print("\n" + "=" * 50)
        print("🎉 Database seeding complete!")
        print("=" * 50)
        print(f"   Users: {len(user_ids)}")
        print(f"   Posts: {post_count}")
        print(f"   Follows: {follow_count}")
        print(f"   Likes: {like_count}")
        print("=" * 50)

    except Exception as e:
        await db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
