from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    owner: str | None = None
