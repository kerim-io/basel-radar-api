# Art Basel Miami - Backend API

Micro social media for Art Basel Miami attendees.

## MVP Features (Phase 1)
- Apple Sign In authentication
- Location-based access (Miami geofence)
- Text-only feed
- User profiles
- Check-ins

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` from `.env.example`:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials:
- Database URL
- Apple Sign In credentials (Team ID, Key ID, Client ID)
- Secret key for JWT

4. Create PostgreSQL database:
```bash
createdb artbasel_db
```

5. Run server:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Auth
- `POST /auth/apple` - Sign in with Apple
- `POST /auth/apple/refresh` - Refresh access token

### Posts
- `POST /posts/` - Create post (text only for MVP)
- `GET /posts/feed` - Get feed
- `GET /posts/by-time?date=YYYY-MM-DD&hour=H` - Get posts by time

### Users
- `GET /users/me` - Get current user
- `PUT /users/me` - Update profile
- `POST /users/follow/{user_id}` - Follow user
- `DELETE /users/follow/{user_id}` - Unfollow user

### Check-ins
- `POST /checkins/` - Check in (requires Basel location)
- `GET /checkins/recent` - Get recent check-ins

## Apple Sign In Setup

1. Create `.p8` key file in Apple Developer Portal
2. Place key file in `keys/` directory
3. Update `.env` with Team ID, Key ID, Client ID
