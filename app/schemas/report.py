from pydantic import BaseModel
from datetime import datetime


class CompletedItemResponse(BaseModel):
    item_type: str  # "task"
    title: str
    project_name: str
    parent_task_title: str | None = None
    assigned_member: str | None = None
    completed_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    period: str
    start: str
    end: str
    items: list[CompletedItemResponse]
    total_count: int
