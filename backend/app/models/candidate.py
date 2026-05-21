from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.job import utc_now


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    years_of_experience: Mapped[float | None] = mapped_column(nullable=True)
    highest_education: Mapped[str | None] = mapped_column(String(120), nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    education: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    work_experiences: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    project_experiences: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    awards: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    self_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)
    low_confidence_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
