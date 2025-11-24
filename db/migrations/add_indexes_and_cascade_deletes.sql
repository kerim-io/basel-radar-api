-- Add indexes on foreign keys for better JOIN performance
-- Add CASCADE deletes for data integrity

-- Follows table
CREATE INDEX IF NOT EXISTS idx_follows_follower_id ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_following_id ON follows(following_id);

ALTER TABLE follows DROP CONSTRAINT IF EXISTS follows_follower_id_fkey;
ALTER TABLE follows ADD CONSTRAINT follows_follower_id_fkey
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE follows DROP CONSTRAINT IF EXISTS follows_following_id_fkey;
ALTER TABLE follows ADD CONSTRAINT follows_following_id_fkey
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE;

-- Posts table
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);

ALTER TABLE posts DROP CONSTRAINT IF EXISTS posts_user_id_fkey;
ALTER TABLE posts ADD CONSTRAINT posts_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Check_ins table
CREATE INDEX IF NOT EXISTS idx_check_ins_user_id ON check_ins(user_id);

ALTER TABLE check_ins DROP CONSTRAINT IF EXISTS check_ins_user_id_fkey;
ALTER TABLE check_ins ADD CONSTRAINT check_ins_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Refresh_tokens table
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);

ALTER TABLE refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_user_id_fkey;
ALTER TABLE refresh_tokens ADD CONSTRAINT refresh_tokens_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Likes table
CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes(user_id);
CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_post_user ON likes(post_id, user_id);

ALTER TABLE likes DROP CONSTRAINT IF EXISTS likes_user_id_fkey;
ALTER TABLE likes ADD CONSTRAINT likes_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE likes DROP CONSTRAINT IF EXISTS likes_post_id_fkey;
ALTER TABLE likes ADD CONSTRAINT likes_post_id_fkey
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;

-- Livestreams table
CREATE INDEX IF NOT EXISTS idx_livestreams_user_id ON livestreams(user_id);

ALTER TABLE livestreams DROP CONSTRAINT IF EXISTS livestreams_user_id_fkey;
ALTER TABLE livestreams ADD CONSTRAINT livestreams_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add comments
COMMENT ON INDEX idx_follows_follower_id IS 'Improves performance for finding all users a specific user follows';
COMMENT ON INDEX idx_follows_following_id IS 'Improves performance for finding all followers of a specific user';
COMMENT ON INDEX idx_posts_user_id IS 'Improves performance for fetching all posts by a user';
COMMENT ON INDEX idx_likes_post_user IS 'Composite index for checking if specific user liked specific post';
