import httpx
from core.config import settings


async def verify_apple_token(code: str, redirect_uri: str) -> dict:
    """
    Verify Apple authorization code and get user info
    Returns dict with user_id and optional email
    """
    url = "https://appleid.apple.com/auth/token"

    data = {
        "client_id": settings.APPLE_CLIENT_ID,
        "client_secret": await generate_client_secret(),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)

        if response.status_code != 200:
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
    Requires private key file in keys/ directory
    """
    from datetime import datetime, timedelta
    from jose import jwt
    import os

    # Load private key (use absolute path)
    from pathlib import Path
    base_dir = Path(__file__).parent.parent
    key_path = base_dir / "keys" / f"{settings.APPLE_KEY_ID}.p8"

    if not key_path.exists():
        raise FileNotFoundError(f"Apple private key not found at {key_path}")

    with open(key_path, "r") as f:
        private_key = f.read()

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
