-- Places feature: Store Google Places data to avoid duplicate API calls
-- Run this migration to add places and google_pics tables

-- Places table
CREATE TABLE IF NOT EXISTS places (
    id SERIAL PRIMARY KEY,
    google_place_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    types TEXT,  -- JSON array of place types
    bounce_count INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Google Pics table (photos for places)
CREATE TABLE IF NOT EXISTS google_pics (
    id SERIAL PRIMARY KEY,
    place_id INTEGER REFERENCES places(id) ON DELETE CASCADE NOT NULL,
    photo_reference VARCHAR(500) NOT NULL,
    photo_url TEXT,
    width INTEGER,
    height INTEGER,
    attributions TEXT,  -- JSON array of attributions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add place_id and google_place_id columns to bounces table
ALTER TABLE bounces ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES places(id) ON DELETE SET NULL;
ALTER TABLE bounces ADD COLUMN IF NOT EXISTS google_place_id VARCHAR(255);

-- Indexes for places
CREATE INDEX IF NOT EXISTS idx_places_google_place_id ON places(google_place_id);
CREATE INDEX IF NOT EXISTS idx_places_location ON places(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_places_bounce_count ON places(bounce_count DESC);

-- Indexes for google_pics
CREATE INDEX IF NOT EXISTS idx_google_pics_place ON google_pics(place_id);

-- Index for bounces
CREATE INDEX IF NOT EXISTS idx_bounces_place_id ON bounces(place_id);
CREATE INDEX IF NOT EXISTS idx_bounces_google_place_id ON bounces(google_place_id);
