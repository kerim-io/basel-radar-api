-- Add anonymous_locations table for real-time location map
-- Users appear on map anonymously, no link to user identity

CREATE TABLE IF NOT EXISTS anonymous_locations (
    location_id UUID PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for efficient cleanup of expired locations (older than 15 minutes)
CREATE INDEX IF NOT EXISTS idx_anonymous_locations_last_updated
ON anonymous_locations(last_updated);

-- Index for spatial queries if needed in future
CREATE INDEX IF NOT EXISTS idx_anonymous_locations_coordinates
ON anonymous_locations(latitude, longitude);
