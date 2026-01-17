import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)


async def verify_apple_token(code: str, redirect_uri: str) -> dict:
    """
    Verify Apple authorization code and get user info
    Returns dict with user_id and optional email
    """
    logger.info(f"Verifying Apple token with redirect_uri: {redirect_uri}")
    url = "https://appleid.apple.com/auth/token"

    try:
        client_secret = await generate_client_secret()
    except Exception as e:
        logger.error(f"Failed to generate client secret: {e}")
        raise

    data = {
        "client_id": settings.APPLE_CLIENT_ID,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    logger.info(f"Sending request to Apple with client_id: {settings.APPLE_CLIENT_ID}")

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)

        if response.status_code != 200:
            logger.error(f"Apple auth failed with status {response.status_code}: {response.text}")
            raise Exception(f"Apple auth failed: {response.text}")

        token_data = response.json()

    # Decode id_token to get user info
    from jose import jwt
    id_token = token_data.get("id_token")
    user_info = jwt.get_unverified_claims(id_token)

    return {
        "user_id": user_info.get("sub"),
        "email": user_info.get("email"),
        "refresh_token": token_data.get("refresh_token")
    }


async def generate_client_secret() -> str:
    """
    Generate client secret JWT for Apple Sign In
    Uses APPLE_KEY_BASE64 from environment or falls back to file
    """
    from datetime import datetime, timedelta
    from jose import jwt
    import base64

    private_key = None

    # Try loading from base64 env var first (Railway)
    apple_key_b64 = getattr(settings, 'APPLE_KEY_BASE64', '') or getattr(settings, 'APNS_KEY_BASE64', '')
    if apple_key_b64:
        try:
            key_b64 = apple_key_b64.strip().replace(" ", "").replace("\n", "")
            key_data = base64.b64decode(key_b64)

            # Check if PEM headers are present, if not wrap the raw key
            if not key_data.startswith(b"-----BEGIN"):
                private_key = (
                    "-----BEGIN PRIVATE KEY-----\n" +
                    key_b64 +
                    "\n-----END PRIVATE KEY-----\n"
                )
                logger.info("Apple key loaded from base64 env var (wrapped with PEM headers)")
            else:
                private_key = key_data.decode('utf-8')
                logger.info("Apple key loaded from base64 env var")
        except Exception as e:
            logger.warning(f"Failed to load Apple key from base64: {e}")

    # Fallback to file if env var not available
    if not private_key:
        from pathlib import Path
        base_dir = Path(__file__).parent.parent
        key_path = base_dir / "keys" / f"{settings.APPLE_KEY_ID}.p8"

        logger.info(f"Looking for Apple key at: {key_path}")

        if not key_path.exists():
            logger.error(f"Apple private key not found at {key_path}")
            raise FileNotFoundError(f"Apple private key not found at {key_path}")

        with open(key_path, "r") as f:
            private_key = f.read()

        logger.info(f"Loaded Apple key from file, length: {len(private_key)} chars")

    headers = {
        "kid": settings.APPLE_KEY_ID,
        "alg": "ES256"
    }

    now = datetime.utcnow()
    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=180)).timestamp()),
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID
    }

    client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    return client_secret


async def refresh_apple_token(refresh_token: str) -> dict:
    """Refresh Apple token"""
    url = "https://appleid.apple.com/auth/token"

    data = {
        "client_id": settings.APPLE_CLIENT_ID,
        "client_secret": await generate_client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        return response.json()
