from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.match import CandidateMatchRead


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None
    phone: str | None
    email: str | None
    city: str | None
    current_company: str | None
    current_title: str | None
    years_of_experience: float | None
    highest_education: str | None
    skills: list[str]
    education: list[dict]
    work_experiences: list[dict]
    project_experiences: list[dict]
    certifications: list[str]
    languages: list[str]
    awards: list[str]
    self_evaluation: str | None
    low_confidence_fields: list[str]
    created_at: datetime
    updated_at: datetime


class CorrectionSource(BaseModel):
    candidate_id: str | None = None
    extractor: str
    confidence: float | None = None
    source_text: str | None = None


class CandidateUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    current_company: str | None = None
    current_title: str | None = None
    years_of_experience: float | None = None
    highest_education: str | None = None
    skills: list[str] | None = None
    education: list[dict] | None = None
    work_experiences: list[dict] | None = None
    project_experiences: list[dict] | None = None
    certifications: list[str] | None = None
    languages: list[str] | None = None
    awards: list[str] | None = None
    self_evaluation: str | None = None
    low_confidence_fields: list[str] | None = None
    correction_sources: dict[str, CorrectionSource] | None = None


class ResumeFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    candidate_id: str | None
    file_name: str
    file_type: str
    file_path: str
    preview_path: str | None
    parsed_text: str | None
    upload_status: str
    parse_status: str
    parse_error: str | None
    created_at: datetime
    updated_at: datetime


class ResumeFieldExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_file_id: str
    candidate_id: str | None
    field_name: str
    extracted_value: str | None
    confidence: float | None
    source_text: str | None
    page_number: int | None
    text_start_offset: int | None
    text_end_offset: int | None
    bounding_box: dict | None
    created_at: datetime


class ResumeParseBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parse_run_id: str
    block_type: str
    title: str | None
    text: str
    start_offset: int | None
    end_offset: int | None
    confidence: float | None
    inferred: bool
    created_at: datetime


class ResumeFieldCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parse_run_id: str
    field_name: str
    value_json: dict | list | str | int | float | bool | None
    source_text: str | None
    extractor: str
    confidence: float | None
    selected: bool
    rejection_reason: str | None
    created_at: datetime


class ResumeParseRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_file_id: str
    candidate_id: str | None
    parser_version: str
    ai_enabled: bool
    status: str
    quality_score: float | None
    warnings: list[str]
    created_at: datetime
    blocks: list[ResumeParseBlockRead] = []
    field_candidates: list[ResumeFieldCandidateRead] = []


class DuplicateCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    job_id: str
    resume_file_id: str
    matched_candidate_id: str
    match_reason: str
    confidence: float
    status: str
    review_note: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    matched_candidate: CandidateRead | None = None


class DuplicateCandidateReviewUpdate(BaseModel):
    status: str
    review_note: str | None = None


class ResumeUploadResult(BaseModel):
    resume_file: ResumeFileRead
    candidate: CandidateRead | None
    field_extractions: list[ResumeFieldExtractionRead]
    duplicate_candidates: list[DuplicateCandidateRead] = []
    duplicate_policy: str = "created_new"


class ResumePreview(BaseModel):
    resume_file_id: str
    file_name: str
    content_type: str
    content: str


class FieldCorrectionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    resume_file_id: str | None
    field_name: str
    old_value: str | None
    new_value: str | None
    editor_id: str | None
    created_at: datetime


class CandidateReviewData(BaseModel):
    candidate: CandidateRead
    resume_file: ResumeFileRead
    preview: ResumePreview
    field_extractions: list[ResumeFieldExtractionRead]
    correction_logs: list[FieldCorrectionLogRead]


class CandidateStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    candidate_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class CandidateStatusUpdate(BaseModel):
    status: str


class CandidateBulkStatusUpdate(BaseModel):
    candidate_ids: list[str]
    status: str


class CandidateBulkActionRequest(BaseModel):
    candidate_ids: list[str]


class CandidateRematchRequest(BaseModel):
    candidate_ids: list[str] | None = None


class CandidateRematchFailure(BaseModel):
    candidate_id: str
    reason: str


class CandidateRematchResult(BaseModel):
    job_id: str
    job_standard_version_id: str | None = None
    total: int
    succeeded: int
    failed: int
    matches: list[CandidateMatchRead] = []
    failures: list[CandidateRematchFailure] = []


class CandidateListItem(BaseModel):
    candidate: CandidateRead
    resume_file: ResumeFileRead
    match: CandidateMatchRead | None = None
    status: CandidateStatusRead | None = None


class CandidateDetail(CandidateListItem):
    preview: ResumePreview
    field_extractions: list[ResumeFieldExtractionRead]
    correction_logs: list[FieldCorrectionLogRead]
    duplicate_candidates: list[DuplicateCandidateRead] = []
