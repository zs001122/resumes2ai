from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.job import utc_now


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    matched_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weak_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interview_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
