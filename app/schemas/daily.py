from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Literal


class TimeEntryCreate(BaseModel):
    entry_date: date
    start_at: datetime
    end_at: datetime
    title: str
    kind: Literal["plan", "actual"] = "plan"
    note: str | None = None
    project_id: int | None = None
    task_id: int | None = None
    color: str | None = None


class TimeEntryUpdate(BaseModel):
    entry_date: date | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    title: str | None = None
    kind: Literal["plan", "actual"] | None = None
    note: str | None = None
    project_id: int | None = None
    task_id: int | None = None
    color: str | None = None


class TimeEntryResponse(BaseModel):
    id: int
    entry_date: date
    start_at: datetime
    end_at: datetime
    title: str
    kind: str
    note: str | None
    project_id: int | None
    task_id: int | None
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyNoteUpsert(BaseModel):
    body: str = Field(default="")


class DailyNoteResponse(BaseModel):
    note_date: date
    body: str
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---- DailyTask (link from a date to an existing Task) ----

class DailyTaskCreate(BaseModel):
    daily_date: date
    task_id: int


class DailyTaskResponse(BaseModel):
    id: int
    daily_date: date
    task_id: int
    position: int
    created_at: datetime
    # Embedded task fields for rendering (live values)
    task_title: str
    task_is_completed: bool
    task_assigned_member: str | None = None
    project_id: int
    project_name: str
