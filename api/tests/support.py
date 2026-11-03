import base64
import os
import time
from datetime import datetime, timedelta, timezone

import jwt

TOKEN_ISSUER = "reqflow-auth"
TOKEN_AUDIENCE = "reqflow-api"
LEGACY_SECRET = "WORKSHOP_SECRET_2026"


def legacy_token(username: str = "student", role: str = "STUDENT", ttl_seconds: int = 3600) -> str:
    raw = f"{username}|{role}|{int(time.time()) + ttl_seconds}|{LEGACY_SECRET}"
    return base64.b64encode(raw.encode()).decode()


def jwt_token(
    username: str = "student",
    role: str = "STUDENT",
    ttl_seconds: int = 3600,
    secret: str | None = None,
    issuer: str = TOKEN_ISSUER,
    audience: str = TOKEN_AUDIENCE,
) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": username,
        "role": role,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(claims, secret or os.environ["WORKSHOP_JWT_SECRET"], algorithm="HS256")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def auth_headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return bearer(jwt_token(username, role))
