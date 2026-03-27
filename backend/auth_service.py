"""
Authentication service for user management.
Handles registration, login, token generation, and Apple Sign In.
"""

import bcrypt
import jwt
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import os

from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv('APP_ENV', 'development').strip().lower() or 'development'
APPLE_JWKS_URL = 'https://appleid.apple.com/auth/keys'


class AuthService:
    """Service for user authentication and token management."""
    
    def __init__(self):
        """Initialize auth service."""
        # JWT secret key (must be stable and explicit in production)
        configured_secret = os.getenv('JWT_SECRET_KEY', '').strip()
        if not configured_secret:
            if APP_ENV == 'production':
                raise RuntimeError('JWT_SECRET_KEY must be set when APP_ENV=production')
            configured_secret = self._generate_secret()
        self.jwt_secret = configured_secret
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
        """Verify Apple Sign In identity token."""
        try:
            allow_insecure_apple_sign_in = os.getenv(
                'ALLOW_INSECURE_APPLE_SIGN_IN',
                'false',
            ).strip().lower() in {'1', 'true', 'yes', 'on'}
            if APP_ENV == 'production' and allow_insecure_apple_sign_in:
                raise RuntimeError(
                    'ALLOW_INSECURE_APPLE_SIGN_IN cannot be enabled when APP_ENV=production',
                )

            if allow_insecure_apple_sign_in:
                payload = jwt.decode(
                    identity_token,
                    options={"verify_signature": False}
                )
            else:
                payload = self._decode_verified_apple_identity_token(identity_token)

            if payload.get('iss') != 'https://appleid.apple.com':
                return None

            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None

            return payload
        except Exception:
            return None

    def _decode_verified_apple_identity_token(self, identity_token: str) -> Dict[str, Any]:
        audiences = self._apple_sign_in_audiences()
        if APP_ENV == 'production' and not audiences:
            raise RuntimeError('APPLE_SIGN_IN_AUDIENCES must be set when APP_ENV=production')

        signing_key = self._apple_signing_key(identity_token)
        decode_kwargs: Dict[str, Any] = {
            'algorithms': ['RS256'],
            'issuer': 'https://appleid.apple.com',
        }
        if audiences:
            decode_kwargs['audience'] = audiences if len(audiences) > 1 else audiences[0]
        else:
            decode_kwargs['options'] = {'verify_aud': False}

        payload = jwt.decode(identity_token, signing_key, **decode_kwargs)
        if not isinstance(payload, dict):
            raise ValueError('Apple identity token payload must be a JSON object')
        return payload

    def _apple_signing_key(self, identity_token: str):
        jwks_client = jwt.PyJWKClient(APPLE_JWKS_URL)
        return jwks_client.get_signing_key_from_jwt(identity_token).key

    def _apple_sign_in_audiences(self) -> List[str]:
        raw = os.getenv('APPLE_SIGN_IN_AUDIENCES', '').strip()
        if raw:
            return [item.strip() for item in raw.split(',') if item.strip()]

        fallbacks = [
            os.getenv('APPLE_SERVICE_ID', '').strip(),
            os.getenv('APPLE_BUNDLE_ID', '').strip(),
            os.getenv('APPLE_CLIENT_ID', '').strip(),
        ]
        return [item for item in fallbacks if item]
    
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
