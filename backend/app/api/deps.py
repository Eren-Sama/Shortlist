"""
Shortlist — API Dependencies

Shared dependencies for route handlers:
- Authentication (Supabase JWT verification)
- Database injection
- Current user extraction

Supports both HS256 (legacy Supabase JWT secret) and
ES256 (modern Supabase JWKS) token verification.
"""

import jwt
import httpx
from typing import Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWK, PyJWKClient

from app.config import get_settings
from app.database import get_supabase
from app.logging_config import get_logger

logger = get_logger("auth")

# Bearer token extractor — auto_error=False allows optional auth
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents a verified authenticated user."""

    def __init__(self, user_id: str, email: str, role: str = "user"):
        self.user_id = user_id
        self.email = email
        self.role = role

    def __repr__(self) -> str:
        return f"AuthenticatedUser(id={self.user_id}, email={self.email})"


@lru_cache(maxsize=1)
def _get_jwks_client() -> Optional[PyJWKClient]:
    """Get a cached JWKS client for Supabase ES256 token verification.
    
    Decorated with @lru_cache so the PyJWKClient (which has its own
    internal key cache with `lifespan=3600`) is created only once
    per process rather than on every request.
    """
    settings = get_settings()
    if not settings.SUPABASE_URL:
        return None
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        return PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    except Exception as e:
        logger.warning(f"Failed to create JWKS client: {e}")
        return None


def _decode_token(token: str) -> dict:
    """
    Decode and verify a Supabase JWT.
    
    Strategy:
    1. Read the token header to determine algorithm (HS256 or ES256)
    2. For HS256: verify with SUPABASE_JWT_SECRET
    3. For ES256: verify with JWKS public key from Supabase
    
    This supports both legacy and modern Supabase auth tokens.
    """
    settings = get_settings()
    
    # Peek at the unverified header to determine algorithm
    try:
        header = jwt.get_unverified_header(token)
    except jwt.DecodeError:
        raise jwt.InvalidTokenError("Malformed token header")
    
    alg = header.get("alg", "HS256")
    
    decode_options = {
        "require": ["exp", "sub", "email"],
        "verify_exp": True,
        "verify_aud": True,
    }
    
    if alg == "HS256":
        # Legacy Supabase tokens signed with shared secret
        if not settings.SUPABASE_JWT_SECRET:
            raise jwt.InvalidTokenError("HS256 verification key not configured")
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options=decode_options,
        )
    elif alg in ("ES256", "RS256", "EdDSA"):
        # Modern Supabase tokens signed with asymmetric key
        jwks_client = _get_jwks_client()
        if not jwks_client:
            raise jwt.InvalidTokenError("JWKS verification not available")
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg],
            audience="authenticated",
            options=decode_options,
        )
    else:
        raise jwt.InvalidTokenError(f"Unsupported JWT algorithm: {alg}")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthenticatedUser:
    """
    Verify Supabase JWT and extract user information.

    Security measures:
    - Validates JWT signature (HS256 or ES256)
    - Checks token expiration
    - Validates audience claim
    - Rejects tokens with invalid structure
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    settings = get_settings()

    if not settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_URL:
        logger.error("No JWT verification method configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    try:
        payload = _decode_token(token)

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")

        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
            )

        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            role=role,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication — returns None if no token provided.
    Use for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
