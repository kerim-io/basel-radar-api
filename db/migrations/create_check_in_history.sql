-- Check-in history: Permanent record of all user venue check-ins
-- Query by user_id for user's check-in history
-- Query by place_id for venue's check-in history

CREATE TABLE IF NOT EXISTS check_in_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    place_id VARCHAR(255) NOT NULL,
    places_fk_id INTEGER REFERENCES places(id) ON DELETE SET NULL,

    -- Denormalized venue info for historical record
    venue_name VARCHAR(255) NOT NULL,
    venue_address VARCHAR(500),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    -- Timestamps
    checked_in_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    checked_out_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_check_in_history_user ON check_in_history(user_id, checked_in_at DESC);
CREATE INDEX IF NOT EXISTS idx_check_in_history_place ON check_in_history(place_id, checked_in_at DESC);
CREATE INDEX IF NOT EXISTS idx_check_in_history_places_fk ON check_in_history(places_fk_id);
CREATE INDEX IF NOT EXISTS idx_check_in_history_time ON check_in_history(checked_in_at DESC);
