from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from app.database import Base


class DailyNote(Base):
    __tablename__ = "daily_notes"

    note_date: Mapped[date] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(default="")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
