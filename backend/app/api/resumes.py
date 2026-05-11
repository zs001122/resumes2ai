import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.correction import FieldCorrectionLog
from app.models.resume import ResumeFieldExtraction, ResumeFile
from app.repositories.jobs import JobRepository
from app.repositories.matches import CandidateMatchRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.v2 import V2Repository
from app.schemas.match import CandidateMatchRead
from app.schemas.resume import (
    CandidateDetail,
    CandidateListItem,
    CandidateRead,
    CandidateReviewData,
    CandidateBulkActionRequest,
    CandidateBulkStatusUpdate,
    CandidateStatusRead,
    CandidateStatusUpdate,
    CandidateUpdate,
    FieldCorrectionLogRead,
    ResumeFieldExtractionRead,
    ResumeFileRead,
    ResumePreview,
    ResumeUploadResult,
)
from app.schemas.v2 import (
    CandidateNoteCreate,
    CandidateNoteRead,
    CandidateTimelineEventCreate,
    CandidateTimelineEventRead,
    TimelineActionType,
    UploadProcessingTaskCreate,
    UploadProcessingTaskRead,
    UploadProcessingTaskUpdate,
)
from app.services.matching import generate_candidate_match
from app.services.match_explanations import build_match_explanations
from app.services.parsers.resume_text import ResumeTextExtractor, UnsupportedResumeFileType
from app.services.resume_parser import parse_resume_text
from app.services.storage.local import LocalStorageService

router = APIRouter(tags=["resumes"])

SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_CANDIDATE_STATUSES = {"pending", "favorite", "pending_contact", "rejected", "archived"}


@router.post(
    "/jobs/{job_id}/resumes/upload",
    response_model=ResumeUploadResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    job_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeUploadResult:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"暂不支持 {suffix or '未知'} 格式，请上传 PDF、DOCX 或 TXT",
        )

    storage = LocalStorageService()
    resume_dir = storage.create_resume_dir()
    original_path = resume_dir / f"original{suffix}"
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过 10MB")
    original_path.write_bytes(contents)

    repository = ResumeRepository(db)
    resume_file = repository.create_resume_file(
        ResumeFile(
            job_id=job_id,
            file_name=file.filename or original_path.name,
            file_type=suffix.lstrip("."),
            file_path=storage.to_relative_path(original_path),
            upload_status="uploaded",
            parse_status="pending",
        )
    )
    v2_repository = V2Repository(db)
    task = v2_repository.create_upload_task(
        UploadProcessingTaskCreate(
            job_id=job_id,
            resume_file_id=resume_file.id,
            original_filename=resume_file.file_name,
            upload_status="uploaded",
            parse_status="pending",
            match_status="pending",
        )
    )

    result = _parse_and_save_resume(repository, resume_file, original_path)
    task = _sync_task_after_parse(v2_repository, task, result)
    if result.candidate:
        job = JobRepository(db).get(job_id)
        candidate = repository.get_candidate(result.candidate.id)
        if job and candidate:
            try:
                match_payload = await generate_candidate_match(job, candidate)
                match_row = CandidateMatchRepository(db).create(job_id, candidate.id, match_payload)
                v2_repository.replace_match_explanations(match_row.id, build_match_explanations(match_row, candidate))
                v2_repository.update_upload_task(
                    task,
                    UploadProcessingTaskUpdate(match_status="success", error_message=None),
                )
                v2_repository.create_timeline_event(
                    CandidateTimelineEventCreate(
                        candidate_id=candidate.id,
                        job_id=job_id,
                        action_type=TimelineActionType.MATCH_SUCCEEDED,
                        action_summary="AI 评分完成",
                        after_value=match_payload.level,
                    )
                )
            except Exception as exc:
                v2_repository.update_upload_task(
                    task,
                    UploadProcessingTaskUpdate(match_status="failed", error_message=f"评分失败：{exc}"),
                )
    return result


@router.get("/jobs/{job_id}/upload-tasks", response_model=list[UploadProcessingTaskRead])
def list_upload_tasks(job_id: str, db: Session = Depends(get_db)) -> list[UploadProcessingTaskRead]:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return [UploadProcessingTaskRead.model_validate(row) for row in V2Repository(db).list_upload_tasks(job_id)]


@router.post("/jobs/{job_id}/upload-tasks/{task_id}/retry", response_model=UploadProcessingTaskRead)
async def retry_upload_task(
    job_id: str,
    task_id: str,
    db: Session = Depends(get_db),
) -> UploadProcessingTaskRead:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    v2_repository = V2Repository(db)
    task = v2_repository.get_upload_task(task_id)
    if not task or task.job_id != job_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传任务不存在")
    task = await _retry_upload_task(db, task_id)
    return UploadProcessingTaskRead.model_validate(task)


@router.post("/jobs/{job_id}/upload-tasks/retry-failed", response_model=list[UploadProcessingTaskRead])
async def retry_failed_upload_tasks(
    job_id: str,
    db: Session = Depends(get_db),
) -> list[UploadProcessingTaskRead]:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    v2_repository = V2Repository(db)
    rows = []
    for task in v2_repository.list_failed_upload_tasks(job_id):
        rows.append(await _retry_upload_task(db, task.id))
    return [UploadProcessingTaskRead.model_validate(row) for row in rows]


@router.get("/resume-files/{resume_file_id}", response_model=ResumeFileRead)
def get_resume_file(resume_file_id: str, db: Session = Depends(get_db)) -> ResumeFileRead:
    resume_file = ResumeRepository(db).get_resume_file(resume_file_id)
    if not resume_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历文件不存在")
    return ResumeFileRead.model_validate(resume_file)


@router.get("/resume-files/{resume_file_id}/preview", response_model=ResumePreview)
def preview_resume_file(resume_file_id: str, db: Session = Depends(get_db)) -> ResumePreview:
    resume_file = ResumeRepository(db).get_resume_file(resume_file_id)
    if not resume_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历文件不存在")
    if resume_file.parsed_text:
        return ResumePreview(
            resume_file_id=resume_file.id,
            file_name=resume_file.file_name,
            content_type="text/plain",
            content=resume_file.parsed_text,
        )
    return ResumePreview(
        resume_file_id=resume_file.id,
        file_name=resume_file.file_name,
        content_type="text/plain",
        content="暂无可预览文本",
    )


@router.post("/resume-files/{resume_file_id}/parse", response_model=ResumeUploadResult)
def parse_resume_file(resume_file_id: str, db: Session = Depends(get_db)) -> ResumeUploadResult:
    repository = ResumeRepository(db)
    resume_file = repository.get_resume_file(resume_file_id)
    if not resume_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历文件不存在")

    path = LocalStorageService().resolve(resume_file.file_path)
    result = _parse_and_save_resume(repository, resume_file, path)
    v2_repository = V2Repository(db)
    task = v2_repository.get_upload_task_for_resume_file(resume_file_id)
    if task:
        _sync_task_after_parse(v2_repository, task, result)
    return result


@router.get("/resume-files/{resume_file_id}/field-extractions", response_model=list[ResumeFieldExtractionRead])
def list_field_extractions(
    resume_file_id: str,
    db: Session = Depends(get_db),
) -> list[ResumeFieldExtractionRead]:
    repository = ResumeRepository(db)
    if not repository.get_resume_file(resume_file_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历文件不存在")
    rows = repository.list_field_extractions(resume_file_id)
    return [ResumeFieldExtractionRead.model_validate(row) for row in rows]


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateListItem])
def list_candidates(
    job_id: str,
    status_filter: str | None = None,
    level: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    city: str | None = None,
    min_years: float | None = None,
    max_years: float | None = None,
    education: str | None = None,
    skill: str | None = None,
    has_risk: bool | None = None,
    low_confidence: bool | None = None,
    archived: bool | None = None,
    db: Session = Depends(get_db),
) -> list[CandidateListItem]:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    repository = ResumeRepository(db)
    match_repository = CandidateMatchRepository(db)
    items: list[CandidateListItem] = []
    for candidate, resume_file in repository.list_candidates_by_job(job_id):
        match = match_repository.latest(job_id, candidate.id)
        candidate_status = repository.get_candidate_status(job_id, candidate.id)
        if status_filter and (candidate_status.status if candidate_status else "pending") != status_filter:
            continue
        if level and (not match or match.level != level):
            continue
        if min_score is not None and (not match or match.score < min_score):
            continue
        if max_score is not None and (not match or match.score > max_score):
            continue
        if city and city not in (candidate.city or ""):
            continue
        if min_years is not None and ((candidate.years_of_experience or 0) < min_years):
            continue
        if (
            max_years is not None
            and candidate.years_of_experience is not None
            and candidate.years_of_experience > max_years
        ):
            continue
        if education and education not in (candidate.highest_education or ""):
            continue
        if skill and skill.lower() not in " ".join(candidate.skills or []).lower():
            continue
        if has_risk is not None and bool(match and match.risks) != has_risk:
            continue
        if low_confidence is not None and bool(candidate.low_confidence_fields) != low_confidence:
            continue
        if archived is not None and ((candidate_status.status if candidate_status else "pending") == "archived") != archived:
            continue
        items.append(
            CandidateListItem(
                candidate=CandidateRead.model_validate(candidate),
                resume_file=ResumeFileRead.model_validate(resume_file),
                match=match,
                status=CandidateStatusRead.model_validate(candidate_status) if candidate_status else None,
            )
        )
    return items


@router.post("/jobs/{job_id}/candidates/bulk-status", response_model=list[CandidateStatusRead])
def bulk_update_candidate_status(
    job_id: str,
    payload: CandidateBulkStatusUpdate,
    db: Session = Depends(get_db),
) -> list[CandidateStatusRead]:
    if payload.status not in ALLOWED_CANDIDATE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的候选人状态")
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    repository = ResumeRepository(db)
    v2_repository = V2Repository(db)
    rows = []
    for candidate_id in payload.candidate_ids:
        if not repository.get_candidate(candidate_id):
            continue
        row = repository.set_candidate_status(job_id, candidate_id, payload.status)
        rows.append(row)
        v2_repository.create_timeline_event(
            CandidateTimelineEventCreate(
                candidate_id=candidate_id,
                job_id=job_id,
                action_type=TimelineActionType.BULK_ACTION,
                action_summary="批量更新候选人状态",
                after_value=payload.status,
            )
        )
    return [CandidateStatusRead.model_validate(row) for row in rows]


@router.post("/jobs/{job_id}/candidates/bulk-add-to-talent-pool", response_model=list[CandidateStatusRead])
def bulk_add_candidates_to_talent_pool(
    job_id: str,
    payload: CandidateBulkActionRequest,
    db: Session = Depends(get_db),
) -> list[CandidateStatusRead]:
    return bulk_update_candidate_status(
        job_id,
        CandidateBulkStatusUpdate(candidate_ids=payload.candidate_ids, status="archived"),
        db,
    )


@router.post("/jobs/{job_id}/candidates/bulk-match", response_model=list[CandidateMatchRead])
async def bulk_create_candidate_matches(
    job_id: str,
    payload: CandidateBulkActionRequest,
    db: Session = Depends(get_db),
) -> list[CandidateMatchRead]:
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    repository = ResumeRepository(db)
    match_repository = CandidateMatchRepository(db)
    v2_repository = V2Repository(db)
    rows = []
    for candidate_id in payload.candidate_ids:
        candidate = repository.get_candidate(candidate_id)
        if not candidate:
            continue
        match_payload = await generate_candidate_match(job, candidate)
        row = match_repository.create(job_id, candidate_id, match_payload)
        v2_repository.replace_match_explanations(row.id, build_match_explanations(row, candidate))
        rows.append(row)
        v2_repository.create_timeline_event(
            CandidateTimelineEventCreate(
                candidate_id=candidate_id,
                job_id=job_id,
                action_type=TimelineActionType.BULK_ACTION,
                action_summary="批量重新评分",
                after_value=match_payload.level,
            )
        )
    return [CandidateMatchRead.model_validate(row) for row in rows]


@router.get("/jobs/{job_id}/candidates/{candidate_id}/notes", response_model=list[CandidateNoteRead])
def list_candidate_notes(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> list[CandidateNoteRead]:
    repository = ResumeRepository(db)
    if not JobRepository(db).get(job_id) or not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    return [CandidateNoteRead.model_validate(row) for row in V2Repository(db).list_notes(candidate_id, job_id)]


@router.post("/jobs/{job_id}/candidates/{candidate_id}/notes", response_model=CandidateNoteRead)
def create_candidate_note(
    job_id: str,
    candidate_id: str,
    payload: CandidateNoteCreate,
    db: Session = Depends(get_db),
) -> CandidateNoteRead:
    repository = ResumeRepository(db)
    if not JobRepository(db).get(job_id) or not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    v2_repository = V2Repository(db)
    row = v2_repository.create_note(
        CandidateNoteCreate(
            candidate_id=candidate_id,
            job_id=job_id,
            content=payload.content,
            created_by=payload.created_by or "local",
        )
    )
    v2_repository.create_timeline_event(
        CandidateTimelineEventCreate(
            candidate_id=candidate_id,
            job_id=job_id,
            action_type=TimelineActionType.NOTE_CREATED,
            action_summary="新增候选人备注",
            after_value=payload.content,
        )
    )
    return CandidateNoteRead.model_validate(row)


@router.get("/jobs/{job_id}/candidates/{candidate_id}/timeline", response_model=list[CandidateTimelineEventRead])
def list_candidate_timeline(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> list[CandidateTimelineEventRead]:
    repository = ResumeRepository(db)
    if not JobRepository(db).get(job_id) or not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    return [
        CandidateTimelineEventRead.model_validate(row)
        for row in V2Repository(db).list_timeline_events(candidate_id, job_id)
    ]


@router.get("/jobs/{job_id}/candidates/{candidate_id}", response_model=CandidateDetail)
def get_candidate_detail(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateDetail:
    repository = ResumeRepository(db)
    candidate = repository.get_candidate(candidate_id)
    resume_file = repository.get_resume_file_for_candidate(job_id, candidate_id)
    if not candidate or not resume_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人或简历不存在")
    candidate_status = repository.get_candidate_status(job_id, candidate_id)
    match = CandidateMatchRepository(db).latest(job_id, candidate_id)
    return CandidateDetail(
        candidate=CandidateRead.model_validate(candidate),
        resume_file=ResumeFileRead.model_validate(resume_file),
        match=match,
        status=CandidateStatusRead.model_validate(candidate_status) if candidate_status else None,
        preview=_preview_from_resume_file(resume_file),
        field_extractions=[
            ResumeFieldExtractionRead.model_validate(row)
            for row in repository.list_field_extractions(resume_file.id)
        ],
        correction_logs=[
            FieldCorrectionLogRead.model_validate(row)
            for row in repository.list_correction_logs(candidate_id)
        ],
    )


@router.patch("/jobs/{job_id}/candidates/{candidate_id}/status", response_model=CandidateStatusRead)
def update_candidate_status(
    job_id: str,
    candidate_id: str,
    payload: CandidateStatusUpdate,
    db: Session = Depends(get_db),
) -> CandidateStatusRead:
    if payload.status not in ALLOWED_CANDIDATE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的候选人状态")
    repository = ResumeRepository(db)
    if not JobRepository(db).get(job_id) or not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    row = repository.set_candidate_status(job_id, candidate_id, payload.status)
    V2Repository(db).create_timeline_event(
        CandidateTimelineEventCreate(
            candidate_id=candidate_id,
            job_id=job_id,
            action_type=TimelineActionType.STATUS_CHANGED,
            action_summary="候选人状态更新",
            after_value=payload.status,
        )
    )
    return CandidateStatusRead.model_validate(row)


@router.get("/jobs/{job_id}/candidates/{candidate_id}/review", response_model=CandidateReviewData)
def get_candidate_review_data(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateReviewData:
    repository = ResumeRepository(db)
    candidate = repository.get_candidate(candidate_id)
    resume_file = repository.get_resume_file_for_candidate(job_id, candidate_id)
    if not candidate or not resume_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人或简历不存在")
    preview = _preview_from_resume_file(resume_file)
    return CandidateReviewData(
        candidate=CandidateRead.model_validate(candidate),
        resume_file=ResumeFileRead.model_validate(resume_file),
        preview=preview,
        field_extractions=[
            ResumeFieldExtractionRead.model_validate(row)
            for row in repository.list_field_extractions(resume_file.id)
        ],
        correction_logs=[
            FieldCorrectionLogRead.model_validate(row)
            for row in repository.list_correction_logs(candidate_id)
        ],
    )


@router.patch("/candidates/{candidate_id}", response_model=CandidateRead)
def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
) -> CandidateRead:
    repository = ResumeRepository(db)
    candidate = repository.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")

    resume_file_id = _latest_resume_file_id(repository, candidate_id)
    logs: list[FieldCorrectionLog] = []
    for key, value in payload.model_dump(exclude_unset=True).items():
        old_value = getattr(candidate, key)
        if old_value == value:
            continue
        setattr(candidate, key, value)
        logs.append(
            FieldCorrectionLog(
                candidate_id=candidate.id,
                resume_file_id=resume_file_id,
                field_name=key,
                old_value=_stringify(old_value),
                new_value=_stringify(value),
                editor_id="local",
            )
        )

    candidate = repository.update_candidate(candidate)
    if logs:
        repository.add_correction_logs(logs)
        v2_repository = V2Repository(db)
        for log in logs:
            v2_repository.create_timeline_event(
                CandidateTimelineEventCreate(
                    candidate_id=candidate.id,
                    job_id=None,
                    action_type=TimelineActionType.FIELD_CORRECTED,
                    action_summary=f"修正字段：{log.field_name}",
                    before_value=log.old_value,
                    after_value=log.new_value,
                )
            )
    return CandidateRead.model_validate(candidate)


@router.get("/candidates/{candidate_id}/correction-logs", response_model=list[FieldCorrectionLogRead])
def list_correction_logs(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> list[FieldCorrectionLogRead]:
    repository = ResumeRepository(db)
    if not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    return [FieldCorrectionLogRead.model_validate(row) for row in repository.list_correction_logs(candidate_id)]


def _parse_and_save_resume(
    repository: ResumeRepository,
    resume_file: ResumeFile,
    original_path: Path,
) -> ResumeUploadResult:
    extractor = ResumeTextExtractor()

    try:
        parsed_text = extractor.extract_text(original_path)
        parsed_resume = parse_resume_text(resume_file.file_name, parsed_text)
        preview_path = original_path.with_name("preview.txt")
        preview_path.write_text(parsed_text, encoding="utf-8")

        candidate = repository.create_candidate(Candidate(**parsed_resume.candidate_data))
        resume_file.candidate_id = candidate.id
        resume_file.parsed_text = parsed_text
        resume_file.preview_path = LocalStorageService().to_relative_path(preview_path)
        resume_file.parse_status = "success"
        resume_file.parse_error = None
        resume_file = repository.update_resume_file(resume_file)

        field_extractions = repository.replace_field_extractions(
            resume_file.id,
            [
                ResumeFieldExtraction(
                    resume_file_id=resume_file.id,
                    candidate_id=candidate.id,
                    **source,
                )
                for source in parsed_resume.field_sources
            ],
        )
        return ResumeUploadResult(
            resume_file=ResumeFileRead.model_validate(resume_file),
            candidate=candidate,
            field_extractions=[
                ResumeFieldExtractionRead.model_validate(row) for row in field_extractions
            ],
        )
    except UnsupportedResumeFileType as exc:
        resume_file.parse_status = "failed"
        resume_file.parse_error = str(exc)
        resume_file = repository.update_resume_file(resume_file)
        return ResumeUploadResult(
            resume_file=ResumeFileRead.model_validate(resume_file),
            candidate=None,
            field_extractions=[],
        )
    except Exception as exc:
        resume_file.parse_status = "failed"
        resume_file.parse_error = f"解析失败：{exc}"
        resume_file = repository.update_resume_file(resume_file)
        return ResumeUploadResult(
            resume_file=ResumeFileRead.model_validate(resume_file),
            candidate=None,
            field_extractions=[],
        )


async def _retry_upload_task(db: Session, task_id: str):
    repository = ResumeRepository(db)
    v2_repository = V2Repository(db)
    task = v2_repository.get_upload_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传任务不存在")
    task = v2_repository.increment_upload_task_retry(task)
    resume_file = repository.get_resume_file(task.resume_file_id) if task.resume_file_id else None
    if not resume_file:
        return v2_repository.update_upload_task(
            task,
            UploadProcessingTaskUpdate(error_message="无法重试：简历文件不存在"),
        )

    if task.parse_status == "failed":
        result = _parse_and_save_resume(repository, resume_file, LocalStorageService().resolve(resume_file.file_path))
        task = _sync_task_after_parse(v2_repository, task, result)

    resume_file = repository.get_resume_file(resume_file.id)
    if resume_file and resume_file.candidate_id and task.match_status == "failed":
        job = JobRepository(db).get(task.job_id)
        candidate = repository.get_candidate(resume_file.candidate_id)
        if job and candidate:
            try:
                match_payload = await generate_candidate_match(job, candidate)
                match_row = CandidateMatchRepository(db).create(task.job_id, candidate.id, match_payload)
                v2_repository.replace_match_explanations(match_row.id, build_match_explanations(match_row, candidate))
                task = v2_repository.update_upload_task(
                    task,
                    UploadProcessingTaskUpdate(match_status="success", error_message=None),
                )
                v2_repository.create_timeline_event(
                    CandidateTimelineEventCreate(
                        candidate_id=candidate.id,
                        job_id=task.job_id,
                        action_type=TimelineActionType.MATCH_SUCCEEDED,
                        action_summary="重新评分完成",
                        after_value=match_payload.level,
                    )
                )
            except Exception as exc:
                task = v2_repository.update_upload_task(
                    task,
                    UploadProcessingTaskUpdate(match_status="failed", error_message=f"评分失败：{exc}"),
                )
    return task


def _sync_task_after_parse(v2_repository: V2Repository, task, result: ResumeUploadResult):
    if result.resume_file.parse_status == "success" and result.candidate:
        task = v2_repository.update_upload_task(
            task,
            UploadProcessingTaskUpdate(parse_status="success", match_status="pending", error_message=None),
        )
        v2_repository.create_timeline_event(
            CandidateTimelineEventCreate(
                candidate_id=result.candidate.id,
                job_id=result.resume_file.job_id,
                action_type=TimelineActionType.PARSE_SUCCEEDED,
                action_summary="简历解析成功",
                after_value=result.resume_file.file_name,
            )
        )
        return task
    return v2_repository.update_upload_task(
        task,
        UploadProcessingTaskUpdate(
            parse_status="failed",
            match_status="skipped",
            error_message=result.resume_file.parse_error or "解析失败",
        ),
    )


def _preview_from_resume_file(resume_file: ResumeFile) -> ResumePreview:
    return ResumePreview(
        resume_file_id=resume_file.id,
        file_name=resume_file.file_name,
        content_type="text/plain",
        content=resume_file.parsed_text or "暂无可预览文本",
    )


def _latest_resume_file_id(repository: ResumeRepository, candidate_id: str) -> str | None:
    resume_file = repository.get_latest_resume_file_for_candidate(candidate_id)
    return resume_file.id if resume_file else None


def _stringify(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
