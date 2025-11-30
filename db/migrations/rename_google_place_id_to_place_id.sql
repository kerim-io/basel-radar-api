-- Migration: Rename google_place_id to place_id across all tables
-- Date: 2024-11-30
-- This standardizes the naming convention for Google Places IDs

-- Step 1: Rename place_id FK columns to places_fk_id first (to avoid conflicts)
ALTER TABLE bounces RENAME COLUMN place_id TO places_fk_id;
ALTER TABLE posts RENAME COLUMN place_id TO places_fk_id;
ALTER TABLE check_ins RENAME COLUMN place_id TO places_fk_id;

-- Step 2: Rename google_place_id to place_id in all tables
ALTER TABLE places RENAME COLUMN google_place_id TO place_id;
ALTER TABLE bounces RENAME COLUMN google_place_id TO place_id;
ALTER TABLE posts RENAME COLUMN google_place_id TO place_id;
ALTER TABLE check_ins RENAME COLUMN google_place_id TO place_id;
