from pydantic import BaseModel
from datetime import datetime


class SubTaskCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_member: str | None = None
    priority: int = 0


class SubTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    assigned_member: str | None = None
    priority: int | None = None
    is_completed: bool | None = None


class SubTaskResponse(BaseModel):
    id: int
    task_id: int
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

    model_config = {"from_attributes": True}
