# Profile Endpoints - Saatchi Aesthetic

## ✅ Backend Ready for iOS ProfileSetupView

### 1. Get Profile
**GET** `/users/me/profile`
**Headers**: `Authorization: Bearer {token}`

**Response**:
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "nickname": "JD",
  "employer": "Art Basel",
  "phone": "+1234567890",
  "email": "john@example.com",
  "profile_picture": "/files/profile_pictures/profile_1_abc123.jpg",
  "has_profile": true
}
```

---

### 2. Update Profile
**PUT** `/users/me/profile`
**Headers**:
- `Authorization: Bearer {token}`
- `Content-Type: application/json`

**Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "nickname": "JD",
  "employer": "Art Basel",
  "phone": "+1234567890",
  "email": "john@example.com",
  "profile_picture_url": "/files/profile_pictures/profile_1_abc123.jpg"
}
```

**Response**: Same as Get Profile

---

### 3. Upload Profile Picture
**POST** `/users/me/profile-picture`
**Headers**:
- `Authorization: Bearer {token}`
- `Content-Type: multipart/form-data`

**Body**: Form data with `file` field (JPEG, PNG, WEBP)

**Response**:
```json
{
  "success": true,
  "profile_picture_url": "/files/profile_pictures/profile_1_abc123.jpg"
}
```

---

### 4. Auth Response Now Includes
**POST** `/auth/apple` or `/auth/passcode`

**Response**:
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com",
  "has_profile": false  // ← NEW FIELD
}
```

---

## iOS Integration Flow

```swift
// 1. Sign in
let authResponse = try await authService.signIn()

// 2. Check has_profile
if !authResponse.hasProfile {
    // Show ProfileSetupView
}

// 3. Upload photo first
let photoURL = try await uploadProfilePicture(image: pickedImage)

// 4. Submit profile
let profileData = ProfileUpdate(
    firstName: "John",
    lastName: "Doe",
    nickname: "JD",
    employer: "Art Basel",
    phone: "+1234567890",
    email: "john@example.com",
    profilePictureUrl: photoURL
)

try await updateProfile(profileData)
```

---

## Database Changes

**User model now has**:
- `first_name` (String, optional)
- `last_name` (String, optional)
- `nickname` (String, optional)
- `employer` (String, optional)
- `phone` (String, optional)
- `email` (String, optional)
- `profile_picture` (String, optional)

**Computed property**:
- `has_profile`: Returns `true` if `first_name`, `last_name`, and `nickname` are set

---

## File Upload Details

- **Allowed types**: JPEG, JPG, PNG, WEBP
- **Storage**: `uploads/profile_pictures/`
- **Filename**: `profile_{user_id}_{uuid}.{ext}`
- **URL format**: `/files/profile_pictures/{filename}`
- **Access**: Public via static files mount

---

## Notes

- All fields optional on update (partial updates supported)
- `has_profile = true` requires: `first_name`, `last_name`, `nickname`
- Phone and email are optional
- Profile picture URL can be set directly or via upload
- Sharp edges, minimalist - backend matches aesthetic
