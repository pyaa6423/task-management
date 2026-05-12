from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime


VALID_STATUS = ("not_started", "in_progress", "done")


class DeliverableCreate(BaseModel):
    title: str
    purpose: str | None = None
    value: str | None = None
    next_action: str | None = None
    target_date: date | None = None
    status: str = "not_started"
    parent_id: int | None = None
    sort_order: int = 0


class DeliverableUpdate(BaseModel):
    title: str | None = None
    purpose: str | None = None
    value: str | None = None
    next_action: str | None = None
    target_date: date | None = None
    status: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class DeliverableResponse(BaseModel):
    id: int
    project_id: int
    parent_id: int | None
    title: str
    purpose: str | None
    value: str | None
    next_action: str | None
    target_date: date | None
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
    children: list[DeliverableResponse] = []

    model_config = {"from_attributes": True}
