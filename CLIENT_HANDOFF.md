# Backend Complete - iOS Client Integration

## ✅ What's Ready

### 1. Auth - Apple Sign In ✅
**Endpoint**: `POST /auth/apple`
**Body**:
```json
{
  "code": "apple_authorization_code",
  "redirect_uri": "your_redirect_uri"
}
```
**Response**:
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user_id": 123,
  "email": "user@example.com"
}
```

### 2. Passcode Fallback ✅
**Endpoint**: `POST /auth/passcode`
**Body**:
```json
{
  "passcode": "ARTBASEL2024",
  "username": "optional_username"
}
```
**Response**: Same as Apple auth

### 3. WebSocket Real-Time Feed ✅
**URL**: `ws://localhost:8001/ws/feed?token={jwt}`

**Initial Connection**:
- Sends `initial_feed` with last 50 posts

**Send New Post**:
```json
{
  "type": "new_post",
  "content": "text content",
  "media_url": null,
  "media_type": null,
  "latitude": null,
  "longitude": null
}
```

**Receive Broadcast**:
```json
{
  "type": "new_post",
  "post": {
    "id": 1,
    "user_id": 123,
    "username": "user123",
    "content": "Hello Basel!",
    "timestamp": "2024-12-01T10:00:00",
    "profile_pic_url": null,
    "media_url": null,
    "media_type": null,
    "latitude": null,
    "longitude": null
  }
}
```

### 4. REST Feed Endpoint ✅
**Endpoint**: `GET /posts/feed?limit=50&offset=0`
**Headers**: `Authorization: Bearer {jwt}`
**Response**:
```json
[
  {
    "id": 1,
    "user_id": 123,
    "username": "user123",
    "content": "Hello!",
    "timestamp": "2024-12-01T10:00:00",
    "profile_pic_url": null,
    "media_url": null,
    "media_type": null
  }
]
```

## 🔧 Backend Setup

```bash
cd /Users/kerim/PycharmProjects/bit_basel_backend
pip install -r requirements.txt
createdb artbasel_db
uvicorn main:app --reload --port 8001
```

## 📡 API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/apple` | POST | No | Apple Sign In |
| `/auth/passcode` | POST | No | Passcode auth (ARTBASEL2024) |
| `/auth/apple/refresh` | POST | No | Refresh token |
| `/posts/feed` | GET | Yes | Get feed (REST) |
| `/posts/` | POST | Yes | Create post |
| `/posts/by-time` | GET | Yes | Timeline scrubbing |
| `/users/me` | GET | Yes | Get profile |
| `/users/me` | PUT | Yes | Update profile |
| `/users/follow/{id}` | POST | Yes | Follow user |
| `/checkins/` | POST | Yes | Check in |
| `/checkins/recent` | GET | Yes | Get check-ins |
| `/ws/feed?token=` | WS | Yes | Real-time feed |

## 🚨 Known Issues Fixed

1. ✅ Auth response matches iOS model (`user_id`, `email`, `token_type`)
2. ✅ Feed response matches iOS model (`timestamp`, `profile_pic_url`)
3. ✅ WebSocket at `/ws/feed` (not `/ws/feed/`)
4. ✅ Passcode fallback auth added
5. ✅ Real-time broadcast on new posts

## 🎯 Next Steps

1. **Production Deploy**: Railway, Render, or AWS
2. **Update iOS baseURL**: From localhost to production
3. **Test with real Apple credentials**
4. **Add media upload** (Phase 2)
5. **Add stories** (Phase 2)
6. **Add live streaming** (Phase 3)

## 📝 Notes

- Database auto-creates tables on startup
- Apple auth needs `.p8` key file in `keys/` directory
- Geofence: 25.7907°N, 80.1300°W, 5km radius (Miami Beach)
- WebSocket broadcasts to all connected clients instantly
