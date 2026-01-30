-- Add optional message column to bounces table
ALTER TABLE bounces ADD COLUMN IF NOT EXISTS message VARCHAR(500);
