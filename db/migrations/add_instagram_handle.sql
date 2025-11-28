-- Add instagram_handle column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS instagram_handle VARCHAR(30);
