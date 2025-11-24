-- Create livestreams table for tracking live streaming sessions
CREATE TABLE IF NOT EXISTS livestreams (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_id VARCHAR(255) UNIQUE NOT NULL,
    post_id VARCHAR(255),

    -- Stream timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,

    -- Stream status: 'active', 'ended', 'error'
    status VARCHAR(20) DEFAULT 'active' NOT NULL,

    -- Viewer statistics
    max_viewers INTEGER DEFAULT 0 NOT NULL,
    total_viewers INTEGER DEFAULT 0 NOT NULL,

    -- Stream metadata
    title VARCHAR(255),
    description TEXT
);

-- Create indexes for efficient queries
CREATE INDEX idx_livestreams_user_id ON livestreams(user_id);
CREATE INDEX idx_livestreams_room_id ON livestreams(room_id);
CREATE INDEX idx_livestreams_status ON livestreams(status);
CREATE INDEX idx_livestreams_started_at ON livestreams(started_at);

-- Add comment
COMMENT ON TABLE livestreams IS 'Tracks live streaming sessions for Art Basel Miami';
