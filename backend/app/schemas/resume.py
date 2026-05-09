from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    low_confidence_fields: list[str]
    created_at: datetime
    updated_at: datetime


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


class ResumeUploadResult(BaseModel):
    resume_file: ResumeFileRead
    candidate: CandidateRead | None
    field_extractions: list[ResumeFieldExtractionRead]


class ResumePreview(BaseModel):
    resume_file_id: str
    file_name: str
    content_type: str
    content: str
