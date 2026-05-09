from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.job import utc_now


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    candidate_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(260), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_status: Mapped[str] = mapped_column(String(24), nullable=False, default="uploaded")
    parse_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ResumeFieldExtraction(Base):
    __tablename__ = "resume_field_extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    resume_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("resume_files.id"), nullable=False)
    candidate_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(120), nullable=False)
    extracted_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
