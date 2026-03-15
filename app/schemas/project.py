from pydantic import BaseModel
from datetime import date, datetime
from app.schemas.task import TaskResponse


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    team_members: list[str] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    team_members: list[str] | None = None
    is_completed: bool | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    team_members: list[str] | None
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tasks: list[TaskResponse] = []

    model_config = {"from_attributes": True}
