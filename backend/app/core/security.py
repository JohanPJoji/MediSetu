"""
Password hashing and JWT token handling.

Per ARCHITECTURE.md §11 (AUTHENTICATION):
- Passwords must never be stored in plaintext -> bcrypt hashing here.
- JWT-based authentication for the prototype -> encode/decode here.
- Secrets must come from environment variables -> JWT_SECRET from Settings.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_SECRET = "dev-insecure-secret-change-me"


def _get_jwt_secret() -> str:
    """
    Resolve the JWT signing secret from settings.

    Falls back to a clearly-named insecure default so local development
    works without a .env file (matching the Phase 1 pattern for
    DATABASE_URL), but refuses to start with that default in a
    non-development environment, and always logs a loud warning when it's
    in use, per ARCHITECTURE.md §11 ("Secrets must come from environment
    variables") and §100 ("Never commit... JWT secrets").
    """
    settings = get_settings()
    if settings.JWT_SECRET:
        return settings.JWT_SECRET

    if settings.ENVIRONMENT.lower() not in ("development", "test", "testing"):
        raise RuntimeError(
            "JWT_SECRET is not set. Refusing to start with the insecure default "
            "outside of a development/test environment. Set JWT_SECRET in your "
            "environment or .env file."
        )

    logger.warning(
        "JWT_SECRET is not set — using an insecure default for local development only. "
        "Set JWT_SECRET in your .env before deploying anywhere shared."
    )
    return _INSECURE_DEFAULT_SECRET


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt. Never store the plaintext."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed hash (e.g. corrupted data) — treat as a failed check,
        # never raise into the caller as an auth bypass surface.
        logger.warning("verify_password: malformed hash encountered")
        return False


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    """
    Issue a signed JWT for the given user id (subject) and role.

    `role` is embedded in the token so authorization checks
    (app.core.dependencies.require_role) don't need a DB round-trip on
    every request — the DB is still consulted once to load the user via
    `get_current_user`, keeping role source-of-truth in the database (the
    token is only a cached claim, re-issued on every login).
    """
    settings = get_settings()
    minutes = expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises jwt.PyJWTError (or a subclass, e.g. ExpiredSignatureError,
    InvalidTokenError) on any invalid/expired/tampered token — callers
    (app.core.dependencies.get_current_user) are responsible for turning
    that into an HTTP 401.
    """
    settings = get_settings()
    return jwt.decode(token, _get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
