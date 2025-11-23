# Likes Feature - Complete ✅

## Endpoints Ready

### 1. Like/Unlike Post (Toggle)
**POST** `/posts/{post_id}/like`
**Headers**: `Authorization: Bearer {token}`

**Response**:
```json
{
  "likes_count": 42,
  "is_liked": true
}
```

**Behavior**: Toggles like
- If not liked → adds like, returns `is_liked: true`
- If already liked → removes like, returns `is_liked: false`

---

### 2. Unlike Post (Explicit)
**DELETE** `/posts/{post_id}/like`
**Headers**: `Authorization: Bearer {token}`

**Response**:
```json
{
  "likes_count": 41,
  "is_liked": false
}
```

---

### 3. Feed with Likes
**GET** `/posts/feed?limit=50&offset=0`
**Headers**: `Authorization: Bearer {token}`

**Response**:
```json
[
  {
    "id": 1,
    "user_id": 123,
    "username": "user123",
    "content": "Hello Basel!",
    "timestamp": "2024-12-01T10:00:00",
    "profile_pic_url": "/files/profile_pictures/profile_123.jpg",
    "media_url": null,
    "media_type": null,
    "latitude": null,
    "longitude": null,
    "likes_count": 42,
    "is_liked_by_current_user": true
  }
]
```

**Fields Added**:
- `likes_count`: Total number of likes
- `is_liked_by_current_user`: Boolean (current user liked this post)

---

### 4. Timeline Scrubbing with Likes
**GET** `/posts/by-time?date=2024-12-01&hour=15`
**Headers**: `Authorization: Bearer {token}`

**Response**: Same format as feed, includes likes

---

## Database Changes

### New Table: `likes`
```sql
CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    post_id INTEGER REFERENCES posts(id),
    created_at TIMESTAMP DEFAULT NOW()
)
```

### Relationships
- `Post.likes` → List of likes
- Cascade delete: Delete post → delete all its likes

---

## Performance Optimization

Feed queries are optimized:
1. **Batch fetch likes counts** for all posts in one query
2. **Batch fetch user's likes** for all posts in one query
3. No N+1 queries
4. Efficient joins and aggregations

---

## iOS Integration

```swift
// Like a post
let response = try await likePost(postId: 123)
print("Likes: \(response.likesCount), Liked: \(response.isLiked)")

// Feed includes likes
struct FeedPost: Codable {
    let id: Int
    let userId: Int
    let username: String
    let content: String
    let timestamp: Date
    let profilePicUrl: String?
    let likesCount: Int              // ← NEW
    let isLikedByCurrentUser: Bool   // ← NEW
}
```

---

## Summary

✅ Like/unlike toggle endpoint
✅ Explicit unlike endpoint
✅ Feed includes likes count
✅ Feed includes is_liked status
✅ Timeline scrubbing includes likes
✅ Optimized batch queries (no N+1)
✅ Database model with cascade delete
✅ Profile endpoints ready
✅ Auth has_profile field

**All iOS requirements met.**
