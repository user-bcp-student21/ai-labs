from collections import Counter
from typing import Any

from app.config import OWNER_MISMATCH_DETAIL
from app.errors import ApiError
from app.repositories import tasks as tasks_repository
from app.schemas import TaskCreate, TaskPriority, TaskStatus

CLOSED_STATUSES = frozenset({TaskStatus.DONE.value, TaskStatus.ARCHIVED.value})


def resolve_owner(requested_owner: str | None, identity_username: str) -> str:
    if not requested_owner:
        return identity_username
    if requested_owner != identity_username:
        raise ApiError(403, OWNER_MISMATCH_DETAIL)
    return requested_owner


def list_tasks(connection: Any, owner: str) -> list[dict[str, Any]]:
    return [to_task_response(row) for row in tasks_repository.find_by_owner(connection, owner)]


def create_task(connection: Any, payload: TaskCreate, identity_username: str) -> dict[str, Any]:
    owner = resolve_owner(payload.owner, identity_username)
    values = (payload.title, payload.description, payload.status.value, owner, payload.priority.value)
    task_id = tasks_repository.insert(connection, values)
    return to_task_response(tasks_repository.find_by_id(connection, task_id))


def summarize(connection: Any, owner: str) -> dict[str, Any]:
    rows = tasks_repository.status_priority_by_owner(connection, owner)
    return {
        "owner": owner,
        "total": len(rows),
        "byStatus": dict(Counter(row["status"] for row in rows)),
        "highPriorityOpen": sum(1 for row in rows if is_open_high_priority(row)),
    }


def is_open_high_priority(row: Any) -> bool:
    return row["priority"] == TaskPriority.HIGH.value and row["status"] not in CLOSED_STATUSES


def to_task_response(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "owner": row["owner"],
        "priority": row["priority"],
        "createdAt": row["created_at"],
    }
