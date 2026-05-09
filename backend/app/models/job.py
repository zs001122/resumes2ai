from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experience_required: Mapped[str | None] = mapped_column(String(120), nullable=True)
    education_required: Mapped[str | None] = mapped_column(String(120), nullable=True)
    jd: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    must_have: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    nice_to_have: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    deal_breakers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scoring_dimensions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
