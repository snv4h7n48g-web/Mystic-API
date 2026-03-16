# Accounts & State Management API Documentation

## 📋 Overview

Complete user accounts system with:
- Email/password registration and login
- Apple Sign In integration
- JWT token authentication
- Reading history and library
- User statistics and insights
- Session linking (anonymous → authenticated)

---

## 🔐 **Authentication Flow**

### Option 1: Email/Password (Traditional)

```
1. Register → POST /v1/auth/register
   Returns: access_token
   
2. Store token in iOS Keychain

3. Use token for authenticated requests
   Header: Authorization: Bearer <token>

4. Logout → POST /v1/auth/logout
```

### Option 2: Apple Sign In (Recommended for iOS)

```
1. iOS: User taps "Sign in with Apple"

2. iOS: Get identity_token from Apple

3. POST /v1/auth/apple
   Returns: access_token
   
4. Store token in iOS Keychain

5. Use token for authenticated requests
```

---

## 📊 **User State Management**

### Anonymous Sessions (Before Login)

```
User opens app
  ↓
Creates anonymous session
  ↓
Gets preview
  ↓
Purchases reading
  ↓
Views reading
  ↓
(Optional) Creates account
  ↓
Links session to account
  ↓
Reading now saved forever
```

### Authenticated Sessions (After Login)

```
User logs in
  ↓
All new sessions automatically linked
  ↓
Can view reading history
  ↓
Can access past readings
  ↓
Stats tracked across all readings
```

---

## 🔌 **API Endpoints**

### 1. Register User (Email/Password)

**Endpoint:** `POST /v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!",
  "display_name": "John Doe",
  "auth_provider": "email"
}
```

**Response:**
```json
{
  "user_id": "uuid-here",
  "email": "user@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-03-02T12:00:00Z"
}
```

**Password Requirements:**
- Minimum 8 characters (enforced client-side)
- Stored as bcrypt hash

---

### 2. Login User (Email/Password)

**Endpoint:** `POST /v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

**Response:**
```json
{
  "user_id": "uuid-here",
  "email": "user@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-03-02T12:00:00Z"
}
```

**Error Responses:**
- `401` - Invalid credentials
- `401` - Account uses Apple Sign In

---

### 3. Apple Sign In

**Endpoint:** `POST /v1/auth/apple`

**Request:**
```json
{
  "identity_token": "eyJraWQiOiJlWGF1bm1...",
  "authorization_code": "c1234567890abcdef...",
  "user_identifier": "001234.a1b2c3d4...",
  "email": "user@privaterelay.appleid.com",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "user_id": "uuid-here",
  "email": "user@privaterelay.appleid.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-03-02T12:00:00Z"
}
```

**Notes:**
- Creates account on first sign in
- Logs in on subsequent sign ins
- Email may be Apple Private Relay address

---

### 4. Logout

**Endpoint:** `POST /v1/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "logged_out"
}
```

**Note:** Currently revokes ALL tokens (logs out from all devices)

---

### 5. Get Current User Profile

**Endpoint:** `GET /v1/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "uuid-here",
  "email": "user@example.com",
  "display_name": "John Doe",
  "auth_provider": "email",
  "role": "user",
  "created_at": "2026-01-15T10:30:00Z",
  "last_login_at": "2026-01-31T08:45:00Z",
  "total_readings": 12,
  "total_spent_usd": 35.88
}
```

---

### 6. Get Reading History

**Endpoint:** `GET /v1/users/me/readings?limit=50&offset=0`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "readings": [
    {
      "session_id": "uuid-1",
      "created_at": "2026-01-30T14:20:00Z",
      "question": "Why do I keep feeling responsible?",
      "status": "complete",
      "purchased_products": ["reading_complete_299"],
      "has_reading": true,
      "preview": { ... },
      "reading": {
        "sections": [ ... ],
        "full_text": "..."
      }
    },
    {
      "session_id": "uuid-2",
      "created_at": "2026-01-28T09:15:00Z",
      "question": "What does my career hold?",
      "status": "complete",
      "purchased_products": ["reading_basic_199"],
      "has_reading": true,
      "preview": { ... },
      "reading": { ... }
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

---

### 7. Link Anonymous Session to Account

**Endpoint:** `POST /v1/sessions/{session_id}/link`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "linked",
  "session_id": "uuid-here",
  "user_id": "uuid-here"
}
```

**Use Case:**
```
User purchases reading anonymously
  ↓
After purchase, prompted to "Save reading"
  ↓
User creates account or logs in
  ↓
Session automatically linked
  ↓
Reading now in their library
```

---

### 8. Get User Statistics

**Endpoint:** `GET /v1/users/me/stats`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "total_sessions": 15,
  "completed_readings": 12,
  "total_readings": 12,
  "total_spent_usd": 35.88,
  "member_since": "2026-01-15T10:30:00Z",
  "insights": {
    "most_common_sun_sign": "Virgo",
    "most_drawn_card": "The Hermit",
    "sun_sign_distribution": {
      "Virgo": 8,
      "Leo": 4,
      "Cancer": 3
    },
    "tarot_frequency": {
      "The Hermit": 5,
      "Justice": 4,
      "The Star": 3,
      "...": "..."
    }
  }
}
```

**Use Cases:**
- Display personalization insights
- "Your most drawn card"
- "You've asked about Virgo energy 8 times"

---

## 🔒 **Authentication Architecture**

### JWT Token Structure

```json
{
  "user_id": "uuid-here",
  "email": "user@example.com",
  "role": "user",
  "exp": 1738156800,
  "iat": 1735564800,
  "jti": "token-uuid"
}
```

**Token Expiration:** 30 days (configurable)

### Token Storage

**Client (iOS):**
- Store in iOS Keychain (secure)
- Send in `Authorization: Bearer <token>` header

**Backend:**
- Token hash stored in `auth_tokens` table
- Can be revoked individually or all at once

### Security Features

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens signed with secret key
- ✅ Tokens can be revoked
- ✅ Token expiration enforced
- ✅ Last used timestamp tracked

---

## 📊 **Database Schema**

### users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    display_name TEXT,
    auth_provider TEXT NOT NULL,  -- 'email', 'apple', 'google'
    provider_user_id TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ,
    total_readings INTEGER DEFAULT 0,
    total_spent_usd NUMERIC(10, 2) DEFAULT 0,
    metadata JSONB
);
```

### user_sessions Table (Link)

```sql
CREATE TABLE user_sessions (
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID NOT NULL REFERENCES sessions(id),
    linked_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, session_id)
);
```

### auth_tokens Table

```sql
CREATE TABLE auth_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash TEXT NOT NULL,
    device_id TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);
```

---

## 🎯 **User Flows**

### Flow 1: Anonymous Purchase → Create Account

```
1. User opens app (no account)
2. POST /v1/sessions → session_id
3. Add birth data
4. POST /v1/sessions/{id}/preview
5. Purchase: POST /v1/sessions/{id}/purchase
6. POST /v1/sessions/{id}/reading → Get reading
7. Prompt: "Save this reading?"
8. POST /v1/auth/register → access_token
9. POST /v1/sessions/{id}/link → Links to account
10. Reading now in library
```

### Flow 2: Logged In User

```
1. User logs in
2. POST /v1/auth/login → access_token
3. Store token
4. Create session with auth header
5. All requests include: Authorization: Bearer <token>
6. Sessions automatically linked to user
7. GET /v1/users/me/readings → View history
```

### Flow 3: Apple Sign In

```
1. User taps "Sign in with Apple"
2. iOS: AuthenticationServices.ASAuthorizationAppleIDProvider
3. iOS: Get identity_token, user_identifier
4. POST /v1/auth/apple → access_token
5. Store token
6. Use for all authenticated requests
```

---

## 🔐 **Route Protection**

### Public Routes (No Auth Required)

- `GET /health`
- `POST /v1/sessions`
- `PATCH /v1/sessions/{id}`
- `POST /v1/sessions/{id}/preview`
- `POST /v1/sessions/{id}/purchase`
- `POST /v1/sessions/{id}/reading`
- `GET /v1/products`

**Rationale:** Allow anonymous purchases (lower friction)

### Protected Routes (Auth Required)

- `GET /v1/auth/me`
- `POST /v1/auth/logout`
- `GET /v1/users/me/readings`
- `GET /v1/users/me/stats`
- `POST /v1/sessions/{id}/link`

**Rationale:** Personal data requires authentication

---

## 💡 **Implementation Details**

### Password Security

```python
# Hashing (on registration)
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verification (on login)
is_valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
```

### JWT Token Generation

```python
payload = {
    'user_id': user_id,
    'email': email,
    'role': role,
    'exp': expiration_time,
    'iat': issued_at_time,
    'jti': unique_token_id
}

token = jwt.encode(payload, secret_key, algorithm='HS256')
```

### Apple Sign In Flow

```
iOS Client
  ↓
Apple Authentication
  ↓
Get: identity_token, user_identifier, email (optional)
  ↓
POST /v1/auth/apple
  ↓
Backend verifies token
  ↓
Create/login user
  ↓
Return access_token
```

---

## 🧪 **Testing Authentication**

### Register New User

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "display_name": "Test User",
    "auth_provider": "email"
  }'

# Save access_token from response
```

### Login Existing User

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Use Token for Protected Routes

```bash
# Get current user profile
curl http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer <your_access_token>"

# Get reading history
curl http://localhost:8000/v1/users/me/readings \
  -H "Authorization: Bearer <your_access_token>"

# Get user stats
curl http://localhost:8000/v1/users/me/stats \
  -H "Authorization: Bearer <your_access_token>"
```

---

## 📱 **iOS Integration**

### Registration Flow (SwiftUI)

```swift
struct RegisterView: View {
    @State private var email = ""
    @State private var password = ""
    
    func register() async {
        let response = try await APIClient.register(
            email: email,
            password: password
        )
        
        // Store token securely
        KeychainHelper.save(token: response.accessToken)
        
        // Navigate to main app
    }
}
```

### Apple Sign In (SwiftUI)

```swift
import AuthenticationServices

struct AppleSignInButton: View {
    func handleAppleSignIn(result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let auth):
            if let appleIDCredential = auth.credential as? ASAuthorizationAppleIDCredential {
                Task {
                    let response = try await APIClient.appleSignIn(
                        identityToken: appleIDCredential.identityToken,
                        userIdentifier: appleIDCredential.user,
                        email: appleIDCredential.email,
                        fullName: appleIDCredential.fullName
                    )
                    
                    KeychainHelper.save(token: response.accessToken)
                }
            }
        case .failure(let error):
            print("Apple Sign In failed: \(error)")
        }
    }
}
```

### Authenticated Requests

```swift
class APIClient {
    static func getReadingHistory() async throws -> [Reading] {
        guard let token = KeychainHelper.getToken() else {
            throw APIError.notAuthenticated
        }
        
        var request = URLRequest(url: URL(string: "\(baseURL)/v1/users/me/readings")!)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode([Reading].self, from: data)
    }
}
```

---

## 🔄 **Session State Management**

### Automatic Linking (Future Enhancement)

```python
# Modify POST /v1/sessions to accept optional user context
@app.post("/v1/sessions")
def create_session(
    payload: SessionCreate,
    user: dict = Depends(get_current_user_optional)
):
    session_id = create_session_logic()
    
    # If user is authenticated, auto-link
    if user:
        user_service.link_session_to_user(user["id"], session_id)
    
    return {"session_id": session_id}
```

### Manual Linking (Current Implementation)

```python
# After anonymous purchase, user creates account
POST /v1/auth/register → access_token

# Then link their session
POST /v1/sessions/{session_id}/link
Header: Authorization: Bearer <token>
```

---

## 📊 **User Statistics Tracking**

Automatically tracked per user:
- `total_readings` - Count of completed readings
- `total_spent_usd` - Lifetime spending
- Reading frequency (from session timestamps)
- Most common sun signs queried
- Most drawn tarot cards
- Purchase patterns

**Use for:**
- Personalization ("You often ask about relationships")
- Marketing ("You haven't had a reading in 30 days")
- Premium upsells ("Power users like you love our monthly subscription")

---

## 🔐 **Security Considerations**

### Production Requirements

**Before Launch:**
1. ✅ Use strong JWT_SECRET_KEY (32+ random bytes)
2. ⚠️ Verify Apple identity tokens with Apple's public keys
3. ⚠️ Add rate limiting on auth endpoints (prevent brute force)
4. ⚠️ Add email verification (send confirmation email)
5. ⚠️ Add password reset flow
6. ⚠️ Use HTTPS only in production
7. ⚠️ Implement CSRF protection

### Current Implementation (MVP)

⚠️ **Development/Testing Only:**
- Apple token verification is basic (not cryptographically verified)
- No rate limiting on login attempts
- No email verification
- No password reset

**These must be added before production launch!**

---

## 💰 **Business Intelligence**

### User Cohorts

Query users by spending:
```sql
-- High value users (>$20)
SELECT * FROM users WHERE total_spent_usd > 20 ORDER BY total_spent_usd DESC;

-- Power users (>10 readings)
SELECT * FROM users WHERE total_readings > 10 ORDER BY total_readings DESC;

-- Recent signups
SELECT * FROM users WHERE created_at > now() - interval '7 days';
```

### Conversion Tracking

```sql
-- Users who registered but never purchased
SELECT u.* 
FROM users u
LEFT JOIN user_sessions us ON u.id = us.user_id
LEFT JOIN sessions s ON us.session_id = s.id
WHERE s.status IS NULL OR s.status = 'draft';
```

---

## 🚀 **Next Steps**

1. ✅ **Accounts API Complete** (you are here)
2. ⏭️ Install new dependencies: `pip install bcrypt PyJWT`
3. ⏭️ Restart server (creates new tables)
4. ⏭️ Test authentication flow
5. ⏭️ Build iOS login screens
6. ⏭️ Add email verification (production)
7. ⏭️ Add password reset flow (production)

---

**Version:** 0.3.0  
**Added:** User accounts, authentication, reading library  
**Date:** 2026-01-31

---

## 📝 **Environment Variables**

Add to `.env`:
```env
JWT_SECRET_KEY=your_random_secret_key_here_change_in_production
```

Generate secure secret:
```python
import secrets
print(secrets.token_urlsafe(32))
```

Or use:
```bash
openssl rand -base64 32
```
