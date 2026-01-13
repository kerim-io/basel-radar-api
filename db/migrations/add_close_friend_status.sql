-- Add close friend status columns to follows table
-- This enables a request/accept flow for close friends

-- Create the enum type for close friend status
DO $$ BEGIN
    CREATE TYPE close_friend_status AS ENUM ('none', 'pending', 'accepted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add the new columns to follows table
ALTER TABLE follows
ADD COLUMN IF NOT EXISTS close_friend_status close_friend_status DEFAULT 'none' NOT NULL;

ALTER TABLE follows
ADD COLUMN IF NOT EXISTS close_friend_requester_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Migrate existing close friends to the new status
-- If is_close_friend is true, set status to 'accepted'
UPDATE follows
SET close_friend_status = 'accepted'
WHERE is_close_friend = true;

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_follows_close_friend_status ON follows(close_friend_status);
CREATE INDEX IF NOT EXISTS idx_follows_close_friend_requester ON follows(close_friend_requester_id);
