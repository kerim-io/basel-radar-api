# Dockerfile for BitBasel C++ Media Server (WebRTC)
# This is a complex build due to WebRTC dependencies

# Stage 1: Builder with all dependencies
FROM ubuntu:22.04 as builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    libboost-all-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source files
COPY CMakeLists.txt .
COPY config.json .
COPY include/ include/
COPY src/ src/

# Note: WebRTC library is complex to build
# This Dockerfile assumes you have WebRTC pre-built binaries
# You would need to either:
# 1. Include pre-built WebRTC libraries in third_party/webrtc/
# 2. Build WebRTC from source (takes hours and requires depot_tools)
# 3. Use a simplified version without WebRTC for basic streaming

# Create build directory and compile
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc)


# Stage 2: Runtime
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libboost-system1.74.0 \
    libboost-thread1.74.0 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy compiled binary from builder
COPY --from=builder /app/build/media_server .
COPY --from=builder /app/build/config.json .

# Create directories
RUN mkdir -p keys logs

# Expose ports
# 9001: HTTP API
# 9002: WebSocket signaling
EXPOSE 9001 9002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Start the media server
CMD ["./media_server"]
