"""Authentication security utilities for MedAlert.

Provides password hashing (bcrypt) and JWT token generation/verification.
Replaces plaintext password storage and mock JWT tokens.

Functions:
    hash_password: Hash a plaintext password with bcrypt
    verify_password: Verify a password against a bcrypt hash
    create_access_token: Generate a signed JWT access token
    decode_access_token: Decode and verify a JWT token
"""

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# bcrypt-based password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _load_jwt_secret() -> str:
    """Read the JWT signing secret, generating an ephemeral one if unset.

    A hardcoded fallback secret is an authentication bypass: the value lives in
    the source tree, so anyone can mint a token with any ``sub`` and any
    ``role``, including a doctor's. Generating a random per-process secret
    instead means an unconfigured deployment invalidates tokens on restart
    (and across workers) rather than silently accepting forged ones.

    Returns:
        The configured secret, or a fresh random one for this process.
    """
    secret = os.getenv("MEDALERT_JWT_SECRET")
    if secret:
        return secret

    logger.warning(
        "MEDALERT_JWT_SECRET is not set; generating an ephemeral signing key. "
        "Issued tokens will not survive a restart and will not validate across "
        "processes. Set MEDALERT_JWT_SECRET before deploying."
    )
    return secrets.token_urlsafe(32)


# JWT configuration - uses env vars with safe defaults for development
JWT_SECRET_KEY = _load_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("MEDALERT_JWT_EXPIRE_MINUTES", "60"))


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain_password: The user's plaintext password.

    Returns:
        Bcrypt hash string suitable for database storage.

    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The password to verify.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if password matches, False otherwise.

    Example:
        >>> hashed = hash_password("test123")
        >>> verify_password("test123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token.

    Args:
        data: Payload dict with claims (e.g., {"sub": user_id, "role": "patient"}).
        expires_delta: Custom expiration time. Defaults to JWT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.

    Example:
        >>> token = create_access_token({"sub": "user123", "role": "patient"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.now(timezone.utc)

    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict]:
    """Decode and verify a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        Decoded payload dict if valid, None if invalid or expired.

    Example:
        >>> token = create_access_token({"sub": "user123", "role": "patient"})
        >>> payload = decode_access_token(token)
        >>> payload["sub"]
        'user123'
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
