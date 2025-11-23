# Quick Start - Art Basel Backend

## Status: MVP Backend Complete ✅

### What's Ready:
- ✅ FastAPI backend structure
- ✅ PostgreSQL with SQLAlchemy async
- ✅ Apple Sign In auth flow
- ✅ JWT token management
- ✅ User profiles
- ✅ Text-only feed
- ✅ Check-ins with geofencing
- ✅ Follow/unfollow users
- ✅ Timeline scrubbing (by date/hour)

### Immediate Next Steps:

1. **Install dependencies**:
```bash
cd /Users/kerim/PycharmProjects/bit_basel_backend
pip install -r requirements.txt
```

2. **Create database**:
```bash
createdb artbasel_db
```

3. **Setup Apple Sign In**:
   - Go to Apple Developer Portal
   - Create Sign In with Apple key (.p8 file)
   - Download and save as `keys/YOUR_KEY_ID.p8`
   - Get: Team ID, Key ID, Client ID

4. **Create .env**:
```bash
cp .env.example .env
# Edit .env with your Apple credentials
```

5. **Run server**:
```bash
uvicorn main:app --reload
```

### Test It:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### API Docs:
http://localhost:8000/docs

---

## Frontend Team Handoff

### Auth Flow:
1. User signs in with Apple (iOS handles this)
2. iOS gets authorization code
3. POST to `/auth/apple` with code
4. Receive `access_token` (use in headers: `Authorization: Bearer TOKEN`)
5. Store `refresh_token` for token renewal

### Key Endpoints:
- **Feed**: `GET /posts/feed?limit=50`
- **Post**: `POST /posts/` (body: `{"content": "text"}`)
- **Check-in**: `POST /checkins/` (requires Miami location)
- **Profile**: `GET /users/me`, `PUT /users/me`

### Geofence:
- Miami Art Basel area: 25.7907°N, 80.1300°W, 5km radius
- Check-ins require location within this area
