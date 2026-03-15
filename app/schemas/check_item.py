from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime


class CheckItemCreate(BaseModel):
    title: str
    inputs: list[str] = []
    outputs: list[str] = []
    results: list[str] = []
    evidences: list[str] = []


class CheckItemUpdate(BaseModel):
    title: str | None = None
    is_checked: bool | None = None
    inputs: list[str] | None = None
    outputs: list[str] | None = None
    results: list[str] | None = None
    evidences: list[str] | None = None


class CheckItemResponse(BaseModel):
    id: int
    task_id: int
    title: str
    is_checked: bool
    checked_at: datetime | None
    inputs: list[str]
    outputs: list[str]
    results: list[str]
    evidences: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
