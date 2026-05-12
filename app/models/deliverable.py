from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from app.database import Base


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("deliverables.id", ondelete="CASCADE"), default=None
    )
    title: Mapped[str] = mapped_column(String(200))
    purpose: Mapped[str | None] = mapped_column(default=None)
    value: Mapped[str | None] = mapped_column(default=None)
    next_action: Mapped[str | None] = mapped_column(default=None)
    target_date: Mapped[date | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="deliverables")
    parent: Mapped["Deliverable | None"] = relationship(
        back_populates="children", remote_side=[id]
    )
    children: Mapped[list["Deliverable"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="deliverable")
