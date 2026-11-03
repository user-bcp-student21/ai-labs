from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import MAX_UPLOAD_BYTES
from app.security import Identity
from app.services import files as files_service


def build_requirements_router(upload_dir: Path, current_identity: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/requirements", status_code=201)
    async def upload_requirement(
        file: UploadFile = File(...), identity: Identity = Depends(current_identity)
    ) -> dict[str, Any]:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        stored = files_service.save_requirement(upload_dir, file.filename, content)
        return {"owner": identity.username, **stored}

    return router
