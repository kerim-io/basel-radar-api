# 🚀 Deploy BitBasel to Railway - DO THIS NOW

Everything is ready! Follow these steps to deploy in the next 10 minutes.

## ✅ Pre-Generated for You

- ✅ **SECRET_KEY**: `0B1rytrChkzawGjS3vAPAVV8-Yht9LGI5tyBhLl3xFA`
- ✅ **QR_SECRET_SALT**: `K1_p7MkQjtEdeXAKIPgoqdtae3nNWgh7gw5Baqp6Npg`
- ✅ **APPLE_PRIVATE_KEY_BASE64**: Ready (see `railway_env_vars.txt`)
- ✅ **Dockerfile**: Created
- ✅ **startup.py**: Created
- ✅ **All configuration files**: Ready

---

## Option 1: Deploy via Railway CLI (Fastest - 5 minutes)

### Step 1: Initialize Project
```bash
cd /Users/kerim/PycharmProjects/bit_basel_backend
railway init
```
- Select: **Empty Project**
- Project name: **bitbasel-backend**

### Step 2: Add PostgreSQL
```bash
railway add --database postgresql
```

### Step 3: Set All Environment Variables
```bash
# Copy and paste this entire block:

railway variables set SECRET_KEY="0B1rytrChkzawGjS3vAPAVV8-Yht9LGI5tyBhLl3xFA"
railway variables set QR_SECRET_SALT="K1_p7MkQjtEdeXAKIPgoqdtae3nNWgh7gw5Baqp6Npg"
railway variables set ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"
railway variables set REFRESH_TOKEN_EXPIRE_DAYS="7"
railway variables set UPLOAD_DIR="uploads"
railway variables set MAX_FILE_SIZE="10485760"
railway variables set APPLE_TEAM_ID="GDZ9V6T9SF"
railway variables set APPLE_KEY_ID="5Y3L2S8R8R"
railway variables set APPLE_CLIENT_ID="com.bitbasel.app"
railway variables set APPLE_REDIRECT_URI="https://bitbasel.app/auth/callback"
railway variables set APPLE_PRIVATE_KEY_BASE64="LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR1RBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJIa3dkd0lCQVFRZ1A3RUJqb2orOUp2K3FZNDcKZ1g4Kzg1T0JZejYyMDNMWEhDYjJ2djNCNUJLZ0NnWUlLb1pJemowREFRZWhSQU5DQUFTUzJkN3AwcGtEUUJzaQp1QmZGVzBjdWhlK3c1bFRwZ1pzSGZTd0xKMFp6NElBdTJvQ1RtR0RwMVhNb1MzTVVBQlgzNGdqeFBLWFhoUTBkCnBaRUNYSU5QCi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K"
railway variables set BASEL_LAT="25.7907"
railway variables set BASEL_LON="-80.1300"
railway variables set BASEL_RADIUS_KM="5"
```

### Step 4: Deploy
```bash
railway up
```

### Step 5: Get Your URL
```bash
railway domain
```

### Step 6: Add Volume (via Dashboard)
1. Open dashboard: `railway open`
2. Click your service
3. Go to **Volumes** tab
4. Click **+ New Volume**
5. Mount Path: `/app/uploads`
6. Size: `1` GB
7. Click **Add**

### Step 7: Test
```bash
# Replace with your actual domain
curl https://bitbasel-backend-production.up.railway.app/health
```

**Expected**: `{"status":"healthy"}`

---

## Option 2: Deploy via Railway Dashboard (10 minutes)

### Step 1: Open Railway
Go to: https://railway.app/new

### Step 2: Deploy from GitHub (or local)

#### Option A: From GitHub (Recommended)
1. First, commit and push your code:
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin kerim
   ```

2. In Railway dashboard:
   - Click **"Deploy from GitHub repo"**
   - Select `bit_basel_backend`
   - Click **Deploy Now**

#### Option B: From Local (if no GitHub)
1. Click **"Deploy from local"**
2. Select this directory
3. Click **Deploy**

### Step 3: Add PostgreSQL
1. In your Railway project, click **+ New**
2. Select **Database** → **PostgreSQL**
3. Wait 30 seconds for provisioning

### Step 4: Configure Environment Variables
1. Click on your service (bitbasel-api)
2. Go to **Variables** tab
3. Click **RAW Editor**
4. Copy the entire contents of `railway_env_vars.txt` and paste
5. Click **Save**

### Step 5: Add Volume
1. In your service, go to **Volumes** tab
2. Click **+ New Volume**
3. Set:
   - Mount Path: `/app/uploads`
   - Size: `1` GB
4. Click **Add**

### Step 6: Wait for Deployment
- Monitor in **Deployments** tab
- Takes ~2-3 minutes

### Step 7: Get Your URL
- In **Settings** tab, find **Domains**
- Click **Generate Domain**
- Copy the URL (e.g., `https://bitbasel-backend-production.up.railway.app`)

### Step 8: Test Deployment
```bash
# Replace with your domain
curl https://your-domain.railway.app/health
curl https://your-domain.railway.app/
```

---

## ✅ Verification Checklist

After deployment, verify:

### 1. Health Check
```bash
curl https://your-app.railway.app/health
# ✓ Should return: {"status":"healthy"}
```

### 2. API Root
```bash
curl https://your-app.railway.app/
# ✓ Should return: {"message":"Art Basel Miami API","status":"running"}
```

### 3. Check Logs
In Railway Dashboard → Your Service → Deployments → Click latest → View logs

Look for:
```
✓ Directory ready: uploads
✓ Directory ready: uploads/profile_pictures
✓ Directory ready: keys
✓ Apple private key decoded and saved to keys/5Y3L2S8R8R.p8
✓ Background cleanup scheduler started (runs every 5 minutes)
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### 4. Database Connection
Check logs for:
```
INFO:     Application startup complete
```

If you see database errors, verify PostgreSQL is running in Railway dashboard.

### 5. Apple Sign-In Setup
Test the auth endpoint:
```bash
curl -I https://your-app.railway.app/auth/apple
# Should redirect to Apple's sign-in page
```

---

## 🐛 Troubleshooting

### Issue: Build fails
**Solution**: Check build logs in Railway dashboard. Most likely missing dependency.

### Issue: "Apple private key not found" in logs
**Solution**:
1. Verify `APPLE_PRIVATE_KEY_BASE64` is set in Variables
2. Value should be: `LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR1RBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJIa3dkd0lCQVFRZ1A3RUJqb2orOUp2K3FZNDcKZ1g4Kzg1T0JZejYyMDNMWEhDYjJ2djNCNUJLZ0NnWUlLb1pJemowREFRZWhSQU5DQUFTUzJkN3AwcGtEUUJzaQp1QmZGVzBjdWhlK3c1bFRwZ1pzSGZTd0xKMFp6NElBdTJvQ1RtR0RwMVhNb1MzTVVBQlgzNGdqeFBLWFhoUTBkCnBaRUNYSU5QCi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K`

### Issue: Database connection error
**Solution**:
1. Check PostgreSQL is running (green status in Railway)
2. `DATABASE_URL` should be auto-set
3. Try restarting the service

### Issue: Can't access /files/... uploads
**Solution**:
1. Verify volume is mounted at `/app/uploads`
2. Check volume isn't full
3. Restart service after adding volume

---

## 📱 Update Your Mobile App

After successful deployment, update your mobile app's API base URL to:
```
https://your-domain.railway.app
```

Test these endpoints:
- `POST /auth/apple` - Apple Sign-In
- `GET /health` - Health check
- `GET /` - API info
- `WS /ws/feed?token=...` - WebSocket feed

---

## 🎉 Success!

Your BitBasel backend is now live on Railway!

**Next Steps:**
1. ✅ Test all API endpoints from your mobile app
2. ✅ Monitor logs: `railway logs` or via dashboard
3. ✅ Set up custom domain (optional) in Railway settings
4. ✅ Configure CORS if needed for web clients

---

## 📊 Monitor Your App

```bash
# View real-time logs
railway logs --tail 100

# Check deployment status
railway status

# Open Railway dashboard
railway open

# Restart service
railway restart
```

---

## 💰 Cost

**Estimated**: $5-10/month
- FastAPI service: ~$3-5
- PostgreSQL: ~$2-3
- 1GB volume: ~$0.25

Monitor usage in Railway dashboard.

---

## 🆘 Need Help?

- Full guide: See `RAILWAY_DEPLOYMENT.md`
- Railway docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

**Generated**: 2024-11-23
**Status**: Ready to deploy! 🚀
