from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_member: str | None = None
    priority: int = 0


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_member: str | None = None
    priority: int | None = None
    is_completed: bool | None = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    parent_id: int | None = None
    title: str
    description: str | None
    start_time: datetime | None
    end_time: datetime | None
    assigned_member: str | None
    priority: int
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    children: list[TaskResponse] = []

    model_config = {"from_attributes": True}
