import os
from collections.abc import Callable
from dataclasses import dataclass

import jwt
from fastapi import Header

from app.config import (
    BEARER_PREFIX,
    INVALID_TOKEN_DETAIL,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    JWT_REQUIRED_CLAIMS,
    JWT_SECRET_ENV,
)
from app.errors import ApiError


@dataclass(frozen=True)
class Identity:
    username: str
    role: str


def load_jwt_secret() -> str:
    secret = os.getenv(JWT_SECRET_ENV, "")
    if not secret:
        raise RuntimeError(f"{JWT_SECRET_ENV} must be set")
    return secret


def build_identity_dependency(secret: str) -> Callable[..., Identity]:
    def current_identity(authorization: str = Header(default="")) -> Identity:
        return _decode_identity(_bearer_token(authorization), secret)

    return current_identity


def _bearer_token(authorization: str) -> str:
    if not authorization.startswith(BEARER_PREFIX):
        raise ApiError(401, INVALID_TOKEN_DETAIL)
    return authorization[len(BEARER_PREFIX):]


def _decode_identity(token: str, secret: str) -> Identity:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": list(JWT_REQUIRED_CLAIMS)},
        )
    except jwt.InvalidTokenError as error:
        raise ApiError(401, INVALID_TOKEN_DETAIL) from error
    return Identity(username=claims["sub"], role=claims["role"])
