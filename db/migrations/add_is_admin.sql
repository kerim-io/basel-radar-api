-- Add is_admin column to users table for admin dashboard access
-- Run this migration: psql $DATABASE_URL -f db/migrations/add_is_admin.sql

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index for faster admin user lookups
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin) WHERE is_admin = TRUE;

-- Optional: Make a specific user admin by email
-- UPDATE users SET is_admin = TRUE WHERE email = 'admin@example.com';
