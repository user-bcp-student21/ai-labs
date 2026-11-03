from pathlib import Path
from typing import Any

from app.config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    UPLOAD_EXISTS_DETAIL,
    UPLOAD_REJECTED_DETAIL,
    UPLOAD_TOO_LARGE_DETAIL,
)
from app.errors import ApiError

UNSAFE_NAMES = frozenset({"", ".", ".."})


def save_requirement(upload_dir: Path, filename: str | None, content: bytes) -> dict[str, Any]:
    safe_name = safe_upload_name(filename)
    ensure_within_size_limit(content)
    target = upload_dir / safe_name
    try:
        with target.open("xb") as handle:
            handle.write(content)
    except FileExistsError as error:
        raise ApiError(409, UPLOAD_EXISTS_DETAIL) from error
    return {"fileName": safe_name, "storedAt": str(target), "size": len(content)}


def safe_upload_name(filename: str | None) -> str:
    name = Path(filename or "").name
    if name in UNSAFE_NAMES or Path(name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ApiError(422, UPLOAD_REJECTED_DETAIL)
    return name


def ensure_within_size_limit(content: bytes) -> None:
    if len(content) > MAX_UPLOAD_BYTES:
        raise ApiError(413, UPLOAD_TOO_LARGE_DETAIL)
