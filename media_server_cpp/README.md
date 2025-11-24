# BitBasel C++ Media Server (WebRTC Livestreaming)

WebRTC-based media server for real-time livestreaming functionality in BitBasel.

## ⚠️ Deployment Notice

**This service is OPTIONAL and has complex dependencies.**

The C++ media server requires:
- WebRTC library (Google's libwebrtc)
- Boost libraries
- OpenSSL
- Significant build time and expertise

### Deployment Options

#### Option 1: Skip Media Server (Recommended for MVP)
- Deploy only the FastAPI backend
- Core social features work perfectly without livestreaming
- Add media server later when needed

#### Option 2: Use Alternative Streaming Solution
Instead of building WebRTC from scratch, consider:
- **Agora.io** - Managed WebRTC service
- **Twilio Live** - Video streaming API
- **AWS IVS** - Amazon Interactive Video Service
- **Mux Live** - Simple livestreaming API

Update `services/media_server_client.py` to integrate with chosen service.

#### Option 3: Deploy This Server (Advanced)

##### Prerequisites
1. Build or obtain WebRTC binaries
2. Place in `third_party/webrtc/` directory with:
   ```
   third_party/webrtc/
   ├── include/      # WebRTC headers
   └── lib/          # WebRTC libraries
   ```

##### Build Locally
```bash
cd media_server_cpp

# Install dependencies (Ubuntu/Debian)
sudo apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libssl-dev

# Create build directory
mkdir -p build && cd build

# Configure and build
cmake ..
make -j$(nproc)

# Run
./media_server
```

##### Deploy to Railway

1. Ensure WebRTC libraries are included in the repository or Docker image
2. Update Dockerfile to include pre-built WebRTC binaries
3. Deploy as separate Railway service:
   ```bash
   railway service create media-server
   ```
4. Configure internal networking between FastAPI and media server

## Configuration

Edit `config.json` to adjust:
- Server ports
- WebRTC ICE servers (STUN/TURN)
- Video/audio codecs and bitrates
- Room limits and timeouts

## API Endpoints

### HTTP API (Port 9001)

```bash
# Health check
GET /health

# Create livestream room
POST /rooms
Body: {"room_id": "user123", "settings": {...}}

# End livestream
DELETE /rooms/{room_id}

# Get room info
GET /rooms/{room_id}

# List active rooms
GET /rooms
```

### WebSocket Signaling (Port 9002)

WebSocket endpoint for WebRTC signaling:
```
ws://localhost:9002/signal/{room_id}
```

Messages:
- `offer` - WebRTC offer from broadcaster
- `answer` - WebRTC answer to viewer
- `ice-candidate` - ICE candidates exchange
- `join` - Viewer joins room
- `leave` - User leaves room

## Integration with FastAPI Backend

The FastAPI backend (`api/routes/livestream.py`) acts as a proxy:

```python
# Start livestream
POST /livestream/start
→ Creates room in media server
→ Returns WebRTC offer

# Join livestream as viewer
POST /livestream/{user_id}/join
→ Connects to media server room
→ Returns WebRTC answer

# End livestream
POST /livestream/end
→ Destroys room in media server
```

## Performance Considerations

- Each room can handle ~100 concurrent viewers (configurable)
- Bandwidth: ~1.5 Mbps per viewer (depends on bitrate)
- CPU intensive: Consider dedicated server or managed service
- TURN server required for NAT traversal in production

## Security

- Enable DTLS encryption (already configured)
- Use TURN server with authentication
- Validate JWT tokens before allowing room access
- Rate limit room creation

## Alternative: Managed Services Comparison

| Service | Pros | Cons | Cost |
|---------|------|------|------|
| **Agora.io** | Easy integration, reliable | Per-minute pricing | ~$0.99/1000 min |
| **Twilio Live** | Good docs, scalable | Higher cost | ~$2/1000 min |
| **AWS IVS** | AWS integration, low latency | AWS ecosystem | ~$1.50/hour streaming |
| **Mux Live** | Simple API, HLS output | Limited WebRTC | ~$0.05/GB |
| **Self-hosted** | Full control, no per-min cost | Complex, maintenance | Server costs only |

## Recommendation

For BitBasel production deployment:

1. **MVP Phase**: Skip media server, deploy only FastAPI backend
2. **Beta Phase**: Integrate with managed service (Agora.io or Twilio)
3. **Scale Phase**: Consider self-hosted if costs justify complexity

## Additional Resources

- [WebRTC Official Site](https://webrtc.org/)
- [Google WebRTC GitHub](https://github.com/webrtc)
- [Agora.io Documentation](https://docs.agora.io/)
- [Twilio Live Documentation](https://www.twilio.com/docs/live)

---

**Status**: Experimental / Optional
**Complexity**: High
**Priority**: Low (core app works without it)
