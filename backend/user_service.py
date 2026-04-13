"""
User service for account management and reading history.
Handles CRUD operations for user accounts.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
import uuid
import os
import json
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        return configured
    if APP_ENV == "production":
        raise RuntimeError("DATABASE_URL must be set when APP_ENV=production")
    return "postgresql+psycopg2://mystic:mysticpass@localhost:5432/mystic"


DATABASE_URL = _database_url()
engine = create_engine(DATABASE_URL, future=True)


class UserService:
    """Service for user account operations."""
    
    def __init__(self):
        """Initialize user service."""
        pass
    
    def create_user(
        self,
        email: str,
        password_hash: Optional[str],
        display_name: Optional[str],
        auth_provider: str,
        provider_user_id: Optional[str] = None
    ) -> str:
        """
        Create a new user account.
        
        Args:
            email: User's email
            password_hash: Hashed password (None for Apple Sign In)
            display_name: User's display name
            auth_provider: Authentication provider (email/apple/google)
            provider_user_id: Provider's user ID (for Apple/Google)
            
        Returns:
            User UUID
        """
        user_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO users (
                    id, email, password_hash, display_name,
                    auth_provider, provider_user_id, role
                )
                VALUES (
                    :id, :email, :password_hash, :display_name,
                    :auth_provider, :provider_user_id, :role
                )
                """),
                {
                    "id": user_id,
                    "email": email,
                    "password_hash": password_hash,
                    "display_name": display_name,
                    "auth_provider": auth_provider,
                    "provider_user_id": provider_user_id,
                    "role": "user"
                }
            )
        
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email}
            ).mappings().first()
        
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by UUID."""
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE id = :id"),
                {"id": user_id}
            ).mappings().first()
        
        return dict(row) if row else None
    
    def get_user_by_provider(
        self,
        auth_provider: str,
        provider_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by auth provider and provider user ID."""
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                SELECT * FROM users 
                WHERE auth_provider = :provider 
                AND provider_user_id = :provider_id
                """),
                {
                    "provider": auth_provider,
                    "provider_id": provider_user_id
                }
            ).mappings().first()
        
        return dict(row) if row else None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        with engine.begin() as conn:
            conn.execute(
                text("""
                UPDATE users 
                SET last_login_at = now() 
                WHERE id = :id
                """),
                {"id": user_id}
            )
    
    def link_session_to_user(self, user_id: str, session_id: str):
        """
        Link a reading session to a user account.
        
        Args:
            user_id: User UUID
            session_id: Session UUID
        """
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO user_sessions (user_id, session_id)
                VALUES (:user_id, :session_id)
                ON CONFLICT DO NOTHING
                """),
                {
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
    
    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all reading sessions for a user.
        
        Args:
            user_id: User UUID
            limit: Max number of sessions to return
            offset: Pagination offset
            
        Returns:
            List of session dicts
        """
        with engine.begin() as conn:
            rows = conn.execute(
                text("""
                SELECT s.*, us.linked_at
                FROM sessions s
                JOIN user_sessions us ON s.id = us.session_id
                WHERE us.user_id = :user_id
                ORDER BY s.created_at DESC
                LIMIT :limit OFFSET :offset
                """),
                {
                    "user_id": user_id,
                    "limit": limit,
                    "offset": offset
                }
            ).mappings().all()
        
        return [dict(row) for row in rows]
    
    def update_user_stats(self, user_id: str, spent_usd: float):
        """
        Update user's reading count and total spent.
        
        Args:
            user_id: User UUID
            spent_usd: Amount spent on this transaction
        """
        with engine.begin() as conn:
            conn.execute(
                text("""
                UPDATE users 
                SET total_readings = total_readings + 1,
                    total_spent_usd = total_spent_usd + :spent
                WHERE id = :id
                """),
                {
                    "id": user_id,
                    "spent": spent_usd
                }
            )

    def get_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get subscription data from user metadata."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        metadata = user.get("metadata") or {}
        return metadata.get("subscription") or {}

    def set_subscription(self, user_id: str, subscription: Dict[str, Any]):
        """Persist subscription data in user metadata."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        metadata = user.get("metadata") or {}
        metadata["subscription"] = subscription
        with engine.begin() as conn:
            conn.execute(
                text("""
                UPDATE users
                SET metadata = CAST(:metadata AS jsonb)
                WHERE id = :id
                """),
                {
                    "id": user_id,
                    "metadata": json.dumps(metadata)
                }
            )
    
    def store_auth_token(
        self,
        user_id: str,
        token: str,
        device_id: Optional[str] = None,
        expires_in_days: int = 30
    ) -> str:
        """
        Store an auth token in the database.
        
        Args:
            user_id: User UUID
            token: JWT token
            device_id: Optional device identifier
            expires_in_days: Token expiration in days
            
        Returns:
            Token ID
        """
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        # Hash the token for storage
        from auth_service import get_auth_service
        auth = get_auth_service()
        token_hash = auth.hash_token(token)
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO auth_tokens (
                    id, user_id, token_hash, device_id, expires_at
                )
                VALUES (
                    :id, :user_id, :token_hash, :device_id, :expires_at
                )
                """),
                {
                    "id": token_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "device_id": device_id,
                    "expires_at": expires_at
                }
            )
        
        return token_id
    
    def verify_and_refresh_token(self, token: str) -> Optional[str]:
        """
        Verify token and update last_used_at.
        
        Args:
            token: JWT token
            
        Returns:
            User ID if valid, None otherwise
        """
        from auth_service import get_auth_service
        auth = get_auth_service()
        
        # Decode and verify JWT
        payload = auth.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        token_hash = auth.hash_token(token)
        
        # Update last used timestamp
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                UPDATE auth_tokens 
                SET last_used_at = now()
                WHERE token_hash = :hash 
                AND user_id = :user_id
                AND expires_at > now()
                RETURNING user_id
                """),
                {
                    "hash": token_hash,
                    "user_id": user_id
                }
            ).mappings().first()
        
        return user_id if result else None
    
    def revoke_token(self, token: str):
        """
        Revoke (delete) an auth token.
        
        Args:
            token: JWT token to revoke
        """
        from auth_service import get_auth_service
        auth = get_auth_service()
        token_hash = auth.hash_token(token)
        
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM auth_tokens WHERE token_hash = :hash"),
                {"hash": token_hash}
            )
    
    def revoke_all_user_tokens(self, user_id: str):
        """
        Revoke all tokens for a user (logout from all devices).
        
        Args:
            user_id: User UUID
        """
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM auth_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )


# Singleton instance
_user_service = None

def get_user_service() -> UserService:
    """Get or create singleton user service."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
