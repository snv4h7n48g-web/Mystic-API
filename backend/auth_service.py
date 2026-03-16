"""
Authentication service for user management.
Handles registration, login, token generation, and Apple Sign In.
"""

import bcrypt
import jwt
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class AuthService:
    """Service for user authentication and token management."""
    
    def __init__(self):
        """Initialize auth service."""
        # JWT secret key (should be in environment)
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', self._generate_secret())
        self.jwt_algorithm = 'HS256'
        self.token_expiry_days = 30
    
    def _generate_secret(self) -> str:
        """Generate a random secret key if none provided."""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored password hash
            
        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str = "user"
    ) -> Dict[str, Any]:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User's UUID
            email: User's email
            role: User's role
            
        Returns:
            Dict with token and expiration
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.token_expiry_days)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': expires_at,
            'iat': datetime.now(timezone.utc),
            'jti': str(uuid.uuid4())  # Token ID for revocation
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return {
            'access_token': token,
            'token_type': 'bearer',
            'expires_at': expires_at.isoformat(),
            'expires_in': self.token_expiry_days * 24 * 3600
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_apple_identity_token(
        self,
        identity_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify Apple Sign In identity token.
        
        In production, this should:
        1. Fetch Apple's public keys
        2. Verify token signature
        3. Validate claims (iss, aud, exp)
        
        For MVP, we'll do basic validation.
        
        Args:
            identity_token: Apple identity token (JWT)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Decode without verification (DEV ONLY)
            # In production, verify signature against Apple's public keys
            payload = jwt.decode(
                identity_token,
                options={"verify_signature": False}
            )
            
            # Basic validation
            if payload.get('iss') != 'https://appleid.apple.com':
                return None
            
            # Check expiration
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            
            return payload
            
        except Exception:
            return None
    
    def hash_token(self, token: str) -> str:
        """
        Hash a token for storage.
        
        Args:
            token: Token string
            
        Returns:
            SHA256 hash of token
        """
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()


# Singleton instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get or create singleton auth service."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
