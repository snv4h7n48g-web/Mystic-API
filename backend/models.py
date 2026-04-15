"""
User accounts and authentication system.
Supports both email/password and Apple Sign In.
"""

import os

import jwt
from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AuthProvider(str, Enum):
    """Authentication provider types."""
    EMAIL = "email"
    APPLE = "apple"
    GOOGLE = "google"  # Future


class UserRole(str, Enum):
    """User role types."""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """User registration payload."""
    email: EmailStr
    password: Optional[str] = None  # None if using Apple Sign In
    display_name: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL
    provider_user_id: Optional[str] = None  # For Apple Sign In


class UserLogin(BaseModel):
    """User login payload."""
    email: EmailStr
    password: str


class AppleSignIn(BaseModel):
    """Apple Sign In payload."""
    identity_token: str
    authorization_code: str
    user_identifier: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

    @model_validator(mode="after")
    def normalize_apple_fields(self):
        allow_insecure = os.getenv(
            "ALLOW_INSECURE_APPLE_SIGN_IN",
            "false",
        ).strip().lower() in {"1", "true", "yes", "on"}

        if not self.user_identifier and allow_insecure:
            try:
                unverified = jwt.decode(self.identity_token, options={"verify_signature": False})
                sub = unverified.get("sub")
                if sub:
                    self.user_identifier = str(sub)
            except Exception:
                pass

        if not self.full_name:
            name = ' '.join(part.strip() for part in [self.given_name or '', self.family_name or ''] if part and part.strip())
            if name:
                self.full_name = name

        if not self.user_identifier:
            raise ValueError('user_identifier is required')

        return self


class UserProfile(BaseModel):
    """User profile response."""
    user_id: str
    email: str
    display_name: Optional[str]
    auth_provider: str
    role: str
    created_at: datetime
    last_login_at: Optional[datetime]
    total_readings: int
    total_spent_usd: float


class SessionLink(BaseModel):
    """Link a session to a user account."""
    session_id: str
    user_id: str


# Database schema for users table
USER_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    display_name TEXT,
    auth_provider TEXT NOT NULL,
    provider_user_id TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ,
    total_readings INTEGER DEFAULT 0,
    total_spent_usd NUMERIC(10, 2) DEFAULT 0,
    birth_date DATE,
    birth_time TEXT,
    birth_time_unknown BOOLEAN,
    birth_location_text TEXT,
    birth_location_normalized TEXT,
    birth_location_verified BOOLEAN DEFAULT false,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(auth_provider, provider_user_id);
"""

# Database schema for user_sessions link table
USER_SESSIONS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    linked_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session ON user_sessions(session_id);
"""

# Database schema for auth tokens
AUTH_TOKENS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    device_id TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);
"""

# Compatibility readings table
COMPATIBILITY_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS compatibility_readings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    person1_data JSONB,
    person2_data JSONB,
    preview JSONB,
    reading JSONB,
    preview_cost_usd NUMERIC(10, 6),
    reading_cost_usd NUMERIC(10, 6),
    purchased BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_compatibility_user ON compatibility_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_compatibility_created ON compatibility_readings(created_at);
"""

# Blessing offerings table
BLESSING_OFFERINGS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS blessing_offerings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    amount_usd NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blessing_offerings_user ON blessing_offerings(user_id);
CREATE INDEX IF NOT EXISTS idx_blessing_offerings_session ON blessing_offerings(session_id);
"""

# Feng Shui analyses table
FENG_SHUI_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS feng_shui_analyses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    analysis_type TEXT,
    room_purpose TEXT,
    user_goals TEXT,
    compass_direction TEXT,
    image_urls JSONB,
    preview JSONB,
    analysis JSONB,
    purchased BOOLEAN DEFAULT false,
    product_id TEXT,
    cost_usd NUMERIC(10, 6),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feng_shui_user ON feng_shui_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_feng_shui_created ON feng_shui_analyses(created_at);
"""
