from typing import Any

from fastapi import APIRouter, Depends, Query

from app.schemas import TaskCreate
from app.security import Identity
from app.services import tasks as tasks_service


def build_tasks_router(connection: Any, current_identity: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/tasks")
    def list_tasks(
        owner: str | None = Query(default=None), identity: Identity = Depends(current_identity)
    ) -> list[dict[str, Any]]:
        owner_name = tasks_service.resolve_owner(owner, identity.username)
        return tasks_service.list_tasks(connection, owner_name)

    @router.post("/api/tasks", status_code=201)
    def create_task(payload: TaskCreate, identity: Identity = Depends(current_identity)) -> dict[str, Any]:
        return tasks_service.create_task(connection, payload, identity.username)

    @router.get("/api/summary")
    def summary(
        owner: str | None = Query(default=None), identity: Identity = Depends(current_identity)
    ) -> dict[str, Any]:
        owner_name = tasks_service.resolve_owner(owner, identity.username)
        return tasks_service.summarize(connection, owner_name)

    return router
