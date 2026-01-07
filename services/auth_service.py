from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Literal
from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token type constants
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT access token with expiration and type claim"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": TOKEN_TYPE_ACCESS,
        "iat": datetime.now(timezone.utc)
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration and type claim"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": TOKEN_TYPE_REFRESH,
        "iat": datetime.now(timezone.utc)
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: Literal["access", "refresh"] = "access") -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or type doesn't match
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # Verify token type if present (backwards compatible with old tokens)
    token_type = payload.get("type")
    if token_type and token_type != expected_type:
        raise JWTError(f"Invalid token type: expected {expected_type}, got {token_type}")

    return payload


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate an access token"""
    return decode_token(token, expected_type=TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Decode and validate a refresh token"""
    return decode_token(token, expected_type=TOKEN_TYPE_REFRESH)
