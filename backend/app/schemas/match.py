from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    candidate_id: str
    job_standard_version_id: str | None = None
    score: float
    level: str
    summary: str
    matched_points: list[str]
    weak_points: list[str]
    risks: list[str]
    interview_questions: list[str]
    created_at: datetime


class CandidateMatchCreate(BaseModel):
    score: float = Field(..., ge=0, le=100)
    level: str
    summary: str
    matched_points: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)


class CandidateRecommendationReport(BaseModel):
    candidate_id: str
    job_id: str
    format: str = "markdown"
    content: str
