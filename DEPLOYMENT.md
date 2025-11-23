# Deployment Guide

## Production Checklist

### 1. Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/artbasel_prod
SECRET_KEY=<generate-secure-random-key>
APPLE_TEAM_ID=<your-team-id>
APPLE_KEY_ID=<your-key-id>
APPLE_CLIENT_ID=com.yourapp.artbasel
APPLE_REDIRECT_URI=https://api.artbasel.app/auth/callback
```

### 2. Database
- PostgreSQL 14+
- Run migrations (auto via `create_db_and_tables()`)
- Enable connection pooling

### 3. Apple Sign In
- Production bundle ID in Apple Developer
- Production redirect URI configured
- `.p8` key file secured on server

### 4. Server Options

#### Option A: Railway.app (Easiest)
```bash
# Connect GitHub repo
# Add PostgreSQL addon
# Set environment variables
# Deploy
```

#### Option B: Render
- Web service from GitHub
- PostgreSQL addon
- Environment variables from dashboard

#### Option C: AWS/GCP
- EC2/Compute Engine
- RDS/Cloud SQL for PostgreSQL
- Load balancer for HTTPS
- Auto-scaling group

### 5. HTTPS
- Required for Apple Sign In
- Use Let's Encrypt or cloud provider SSL

### 6. Monitoring
- Health endpoint: `/health`
- Database connection pooling metrics
- Error logging to Sentry/CloudWatch

### 7. Rate Limiting
Add to production:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

### 8. CORS
Update for production domains:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://artbasel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
