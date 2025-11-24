# ✅ DEPLOYMENT READY - Your BitBasel Backend

## 🎉 Everything is Prepared and Ready to Deploy!

All configuration files have been created and your production secrets have been generated.

---

## 🚀 QUICK START - Choose Your Method

### Method 1: Automated Script (Easiest - 5 minutes)
```bash
./RUN_THIS_TO_DEPLOY.sh
```

This script will:
- ✅ Initialize Railway project
- ✅ Add PostgreSQL database
- ✅ Set all environment variables
- ✅ Deploy your application
- ✅ Get your public URL

Then manually add the volume via Railway dashboard.

---

### Method 2: Step-by-Step Commands
```bash
# 1. Initialize
railway init
#    Select: Empty Project
#    Name: bitbasel-backend

# 2. Add database
railway add --database postgresql

# 3. Set variables (copy from railway_env_vars.txt)
railway variables set SECRET_KEY="0B1rytrChkzawGjS3vAPAVV8-Yht9LGI5tyBhLl3xFA"
# ... (see railway_env_vars.txt for all variables)

# 4. Deploy
railway up

# 5. Get URL
railway domain

# 6. Add volume via dashboard
railway open
```

---

### Method 3: Railway Dashboard (Web UI)
See: `DEPLOY_NOW.md` for complete web UI instructions.

---

## 📁 Generated Files

| File | Purpose |
|------|---------|
| `RUN_THIS_TO_DEPLOY.sh` | **Run this!** Automated deployment script |
| `DEPLOY_NOW.md` | Complete deployment instructions |
| `railway_env_vars.txt` | All environment variables (ready to copy) |
| `Dockerfile` | Docker configuration for FastAPI |
| `startup.py` | Application startup with scheduler |
| `railway.toml` | Railway service configuration |
| `.dockerignore` | Optimized Docker build |
| `RAILWAY_DEPLOYMENT.md` | Full documentation (50+ pages) |
| `RAILWAY_QUICKSTART.md` | 15-minute quick start guide |

---

## 🔐 Generated Secrets (Already Configured)

✅ **SECRET_KEY**: `0B1rytrChkzawGjS3vAPAVV8-Yht9LGI5tyBhLl3xFA`
✅ **QR_SECRET_SALT**: `K1_p7MkQjtEdeXAKIPgoqdtae3nNWgh7gw5Baqp6Npg`
✅ **APPLE_PRIVATE_KEY_BASE64**: Encoded and ready (see railway_env_vars.txt)

These are already included in the deployment script and env vars file.

---

## ✅ Pre-Deployment Checklist

- [x] Dockerfile created
- [x] startup.py created with Apple key decoder + scheduler
- [x] Environment variables generated
- [x] Apple private key encoded to base64
- [x] .dockerignore optimized
- [x] railway.toml configured
- [x] Documentation complete
- [x] APScheduler added to requirements.txt
- [ ] **YOU: Run deployment script or follow DEPLOY_NOW.md**
- [ ] **YOU: Add volume via Railway dashboard**

---

## 🎯 What Happens When You Deploy

1. **Railway builds Docker image** (~2-3 minutes)
   - Installs Python 3.11.2
   - Installs all dependencies
   - Creates optimized production image

2. **startup.py runs on container start**:
   - ✓ Creates directories (uploads, keys)
   - ✓ Decodes Apple private key from env var
   - ✓ Starts background location cleanup (every 5 min)
   - ✓ Launches uvicorn on Railway's PORT

3. **Database tables auto-created**:
   - users, posts, check_ins, follows, likes
   - refresh_tokens, anonymous_locations

4. **Your API goes live**:
   - Health check: `/health`
   - Root: `/`
   - WebSocket: `/ws/feed`
   - All routes active

---

## 🧪 How to Test After Deployment

```bash
# Get your URL (replace with actual)
DOMAIN="https://bitbasel-backend-production.up.railway.app"

# Test health
curl $DOMAIN/health
# Expected: {"status":"healthy"}

# Test API root
curl $DOMAIN/
# Expected: {"message":"Art Basel Miami API","status":"running"}

# View logs
railway logs --tail 50

# Open dashboard
railway open
```

---

## 📱 Update Mobile App

After deployment, update your app's API base URL to your Railway domain:

```swift
// iOS
let apiBaseURL = "https://your-domain.railway.app"
```

Test endpoints:
- ✅ `POST /auth/apple` - Sign in with Apple
- ✅ `GET /users/me` - Get user profile
- ✅ `POST /posts` - Create post
- ✅ `WS /ws/feed?token=...` - Real-time feed

---

## 💰 Expected Costs

**Railway Starter Plan**: ~$5-10/month
- FastAPI service: ~$3-5
- PostgreSQL database: ~$2-3
- 1GB volume storage: ~$0.25

**Free trial**: Railway gives $5 credit to start.

---

## 🆘 If Something Goes Wrong

### Build Fails
- Check build logs in Railway dashboard
- Verify Dockerfile syntax
- Ensure all dependencies in requirements.txt

### "Apple private key not found"
- Verify `APPLE_PRIVATE_KEY_BASE64` is set correctly
- Value should start with: `LS0tLS1CRUdJTi...`

### Database Connection Error
- Check PostgreSQL is running (green in Railway)
- DATABASE_URL is auto-set by Railway
- Try restarting service

### File Uploads Don't Persist
- Add volume at `/app/uploads` via dashboard
- Restart service after adding volume

**Full troubleshooting**: See `RAILWAY_DEPLOYMENT.md`

---

## 📚 Documentation Index

- **START HERE**: `DEPLOY_NOW.md` - Step-by-step deployment
- **Quick Reference**: `RAILWAY_QUICKSTART.md` - 15-min guide
- **Full Docs**: `RAILWAY_DEPLOYMENT.md` - Complete reference
- **Env Vars**: `railway_env_vars.txt` - Copy-paste ready
- **Media Server**: `media_server_cpp/README.md` - Optional livestreaming

---

## 🎯 Recommended Deployment Path

1. **Now**: Deploy FastAPI backend only (skip media server)
2. **Test**: Verify all core features work
3. **Later**: Add managed livestreaming (Agora/Twilio) if needed
4. **Scale**: Monitor usage and upgrade Railway plan as needed

---

## ⏭️ NEXT STEP

Run this command now:

```bash
./RUN_THIS_TO_DEPLOY.sh
```

Or open `DEPLOY_NOW.md` for detailed instructions.

---

**Status**: ✅ READY TO DEPLOY
**Generated**: 2024-11-23
**Time to Deploy**: 5-10 minutes

🚀 **Let's go!**
