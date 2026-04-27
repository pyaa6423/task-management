from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from app.database import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_date: Mapped[date] = mapped_column(index=True)
    start_at: Mapped[datetime] = mapped_column()
    end_at: Mapped[datetime] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="plan")  # "plan" or "actual"
    note: Mapped[str | None] = mapped_column(default=None)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), default=None
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), default=None
    )
    color: Mapped[str | None] = mapped_column(String(20), default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
