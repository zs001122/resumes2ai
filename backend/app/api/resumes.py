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
from app.schemas.resume import (
    CandidateDetail,
    CandidateListItem,
    CandidateRead,
    CandidateReviewData,
    CandidateStatusRead,
    CandidateStatusUpdate,
    CandidateUpdate,
    FieldCorrectionLogRead,
    ResumeFieldExtractionRead,
    ResumeFileRead,
    ResumePreview,
    ResumeUploadResult,
)
from app.services.matching import generate_candidate_match
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

    result = _parse_and_save_resume(repository, resume_file, original_path)
    if result.candidate:
        job = JobRepository(db).get(job_id)
        candidate = repository.get_candidate(result.candidate.id)
        if job and candidate:
            match_payload = await generate_candidate_match(job, candidate)
            CandidateMatchRepository(db).create(job_id, candidate.id, match_payload)
    return result


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
    return _parse_and_save_resume(repository, resume_file, path)


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
        items.append(
            CandidateListItem(
                candidate=CandidateRead.model_validate(candidate),
                resume_file=ResumeFileRead.model_validate(resume_file),
                match=match,
                status=CandidateStatusRead.model_validate(candidate_status) if candidate_status else None,
            )
        )
    return items


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
