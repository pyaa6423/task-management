from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime


class EventCreate(BaseModel):
    title: str
    event_date: date
    description: str | None = None
    project_id: int | None = None
    color: str | None = "#e60012"


class EventUpdate(BaseModel):
    title: str | None = None
    event_date: date | None = None
    description: str | None = None
    project_id: int | None = None
    color: str | None = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: str | None
    event_date: date
    project_id: int | None
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
