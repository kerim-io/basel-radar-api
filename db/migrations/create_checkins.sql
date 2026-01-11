-- Current active check-ins only. One per user.
-- When user checks into new venue, old record is deleted.

CREATE TABLE IF NOT EXISTS checkins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    place_id VARCHAR(255) NOT NULL,
    places_fk_id INTEGER REFERENCES places(id) ON DELETE SET NULL,

    venue_name VARCHAR(255) NOT NULL,
    venue_address VARCHAR(500),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    checked_in_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_place ON checkins(place_id);
CREATE INDEX IF NOT EXISTS idx_checkins_places_fk ON checkins(places_fk_id);
CREATE INDEX IF NOT EXISTS idx_checkins_last_seen ON checkins(last_seen_at);
