from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.match import CandidateMatchRead
from app.schemas.resume import CandidateRead


class TimelineActionType(StrEnum):
    UPLOAD_CREATED = "upload_created"
    UPLOAD_FAILED = "upload_failed"
    PARSE_SUCCEEDED = "parse_succeeded"
    PARSE_FAILED = "parse_failed"
    MATCH_SUCCEEDED = "match_succeeded"
    MATCH_FAILED = "match_failed"
    FIELD_CORRECTED = "field_corrected"
    STATUS_CHANGED = "status_changed"
    NOTE_CREATED = "note_created"
    TALENT_POOL_ADDED = "talent_pool_added"
    TALENT_POOL_REMOVED = "talent_pool_removed"
    BULK_ACTION = "bulk_action"


class UploadProcessingTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    resume_file_id: str | None
    original_filename: str
    upload_status: str
    parse_status: str
    match_status: str
    error_message: str | None
    retry_count: int
    duplicate_count: int = 0
    has_duplicate_risk: bool = False
    created_at: datetime
    updated_at: datetime


class UploadProcessingTaskCreate(BaseModel):
    job_id: str
    original_filename: str
    resume_file_id: str | None = None
    upload_status: str = "pending"
    parse_status: str = "pending"
    match_status: str = "pending"
    error_message: str | None = None


class UploadProcessingTaskUpdate(BaseModel):
    resume_file_id: str | None = None
    upload_status: str | None = None
    parse_status: str | None = None
    match_status: str | None = None
    error_message: str | None = None
    retry_count: int | None = None
    duplicate_count: int | None = None
    has_duplicate_risk: bool | None = None


class CandidateMatchExplanationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    match_id: str
    dimension: str
    score: float | None
    conclusion: str
    evidence_text: str | None
    confidence: float | None
    created_at: datetime


class CandidateMatchExplanationCreate(BaseModel):
    dimension: str
    score: float | None = Field(default=None, ge=0, le=100)
    conclusion: str
    evidence_text: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class CandidateNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    job_id: str | None
    content: str
    created_by: str | None
    created_at: datetime


class CandidateNoteCreate(BaseModel):
    candidate_id: str
    job_id: str | None = None
    content: str
    created_by: str | None = None


class CandidateTimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    job_id: str | None
    action_type: str
    action_summary: str
    before_value: str | None
    after_value: str | None
    metadata_json: dict
    created_at: datetime


class CandidateTimelineEventCreate(BaseModel):
    candidate_id: str
    job_id: str | None = None
    action_type: TimelineActionType | str
    action_summary: str
    before_value: str | None = None
    after_value: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class CandidateTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime


class CandidateTagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class CandidateTagLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    tag_id: str
    created_at: datetime


class TalentPoolUpdate(BaseModel):
    job_id: str | None = None


class CandidateJobHistoryItem(BaseModel):
    job_id: str
    job_title: str
    job_status: str
    candidate_status: str
    updated_at: datetime


class TalentPoolCandidateRead(BaseModel):
    candidate: CandidateRead
    tags: list[CandidateTagRead] = Field(default_factory=list)
    job_history: list[CandidateJobHistoryItem] = Field(default_factory=list)
    latest_match: CandidateMatchRead | None = None
