# ✅ Server Running on http://localhost:8001

## Status: LIVE

**Health**: http://localhost:8001/health
```json
{"status":"healthy"}
```

**API Docs**: http://localhost:8001/docs

**Base URL for iOS**: `http://localhost:8001`

---

## Available Endpoints

### Auth
- `POST /auth/apple` - Apple Sign In
- `POST /auth/passcode` - Passcode auth (ARTBASEL2024)
- `POST /auth/apple/refresh` - Refresh token

### Posts
- `GET /posts/feed` - Get feed (with likes)
- `POST /posts/` - Create post
- `GET /posts/by-time` - Timeline scrubbing

### Likes
- `POST /posts/{post_id}/like` - Like/unlike (toggle)
- `DELETE /posts/{post_id}/like` - Unlike

### Profile
- `GET /users/me/profile` - Get profile
- `PUT /users/me/profile` - Update profile
- `POST /users/me/profile-picture` - Upload photo

### Users
- `GET /users/me` - Get current user
- `POST /users/follow/{user_id}` - Follow
- `DELETE /users/follow/{user_id}` - Unfollow

### Check-ins
- `POST /checkins/` - Check in
- `GET /checkins/recent` - Recent check-ins

### WebSocket
- `ws://localhost:8001/ws/feed?token={jwt}` - Real-time feed

---

## Database
- **PostgreSQL**: `artbasel_db`
- **Tables auto-created** on startup
- **Models**: User, Post, Like, CheckIn, Follow, RefreshToken

---

## Test It

```bash
# Health check
curl http://localhost:8001/health

# API docs (browser)
open http://localhost:8001/docs

# Test passcode auth
curl -X POST http://localhost:8001/auth/passcode \
  -H "Content-Type: application/json" \
  -d '{"passcode": "ARTBASEL2024", "username": "testuser"}'
```

---

## Server Info
- **Host**: 0.0.0.0
- **Port**: 8001
- **Reload**: Enabled (auto-restart on code changes)
- **Process ID**: Check with `lsof -ti:8001`

---

## Stop Server
```bash
lsof -ti:8001 | xargs kill -9
```

---

## iOS Client Ready
Update iOS `baseURL` to:
```swift
private let baseURL = "http://localhost:8001"
```

All endpoints match iOS models perfectly.
