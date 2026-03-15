from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), default=None
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(default=None)
    start_time: Mapped[datetime | None] = mapped_column(default=None)
    end_time: Mapped[datetime | None] = mapped_column(default=None)
    assigned_member: Mapped[str | None] = mapped_column(String(100), default=None)
    priority: Mapped[int] = mapped_column(default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="tasks")
    parent: Mapped["Task | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Task"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
