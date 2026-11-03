import os

from app.config import CORS_ORIGINS_ENV, CORS_ORIGINS_SEPARATOR, CORS_WILDCARD, DEFAULT_CORS_ORIGINS


def load_cors_origins() -> list[str]:
    raw_value = os.getenv(CORS_ORIGINS_ENV, "")
    origins = [origin.strip() for origin in raw_value.split(CORS_ORIGINS_SEPARATOR) if origin.strip()]
    if CORS_WILDCARD in origins:
        raise RuntimeError(f"{CORS_ORIGINS_ENV} must list explicit origins, not '{CORS_WILDCARD}'")
    return origins or list(DEFAULT_CORS_ORIGINS)
