import os
from typing import Any

from fastapi import APIRouter, Depends

from app.config import AUTH_HEALTH_URL_ENV, DEFAULT_AUTH_HEALTH_URL
from app.security import Identity
from app.services import health as health_service


def build_health_router(current_identity: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/backend-health")
    def backend_health(identity: Identity = Depends(current_identity)) -> dict[str, Any]:
        url = os.getenv(AUTH_HEALTH_URL_ENV, DEFAULT_AUTH_HEALTH_URL)
        status, body = health_service.fetch_backend_health(url)
        return {"requestedBy": identity.username, "status": status, "body": body}

    return router
