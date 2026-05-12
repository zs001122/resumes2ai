from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.resume import ResumeFile
from app.models.status import CandidateJobStatus
from app.repositories.jobs import JobRepository
from app.repositories.jobs import changed_standard_fields, job_standard_criteria
from app.repositories.v2 import V2Repository
from app.schemas.job import (
    JDParseRequest,
    JDParseResult,
    JDQualityCheck,
    JobCreate,
    JobFunnelStats,
    JobListItem,
    JobRead,
    JobStandardVersionRead,
    JobUpdate,
)
from app.services.jobs import check_jd_quality, parse_jd_locally

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse-jd", response_model=JDParseResult)
def parse_jd(payload: JDParseRequest) -> JDParseResult:
    return parse_jd_locally(payload)


@router.get("", response_model=list[JobListItem])
def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[JobListItem]:
    jobs = JobRepository(db).list(status=status_filter)
    return [JobListItem.model_validate(job) for job in jobs]


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> JobRead:
    job = JobRepository(db).create(payload)
    V2Repository(db).create_job_standard_version(job.id, job_standard_criteria(job), "创建岗位初始标准")
    return JobRead.model_validate(job)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return JobRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    if job.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已关闭岗位不能编辑，请复制岗位后修改")
    standard_changes = changed_standard_fields(job, payload)
    updated = repository.update(job, payload)
    if standard_changes:
        V2Repository(db).create_job_standard_version(
            updated.id,
            job_standard_criteria(updated),
            f"更新岗位标准：{', '.join(standard_changes)}",
        )
    return JobRead.model_validate(updated)


@router.post("/{job_id}/close", response_model=JobRead)
def close_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return JobRead.model_validate(repository.close(job))


@router.post("/{job_id}/copy", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def copy_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    copied = repository.copy(job)
    V2Repository(db).create_job_standard_version(copied.id, job_standard_criteria(copied), "复制岗位初始标准")
    return JobRead.model_validate(copied)


@router.post("/{job_id}/pause", response_model=JobRead)
def pause_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return JobRead.model_validate(repository.set_status(job, "paused"))


@router.post("/{job_id}/reopen", response_model=JobRead)
def reopen_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    if job.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已关闭岗位不能重新开放，请复制岗位后修改")
    return JobRead.model_validate(repository.set_status(job, "open"))


@router.get("/{job_id}/funnel", response_model=JobFunnelStats)
def get_job_funnel(job_id: str, db: Session = Depends(get_db)) -> JobFunnelStats:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    status_rows = db.execute(
        select(CandidateJobStatus.status, func.count())
        .where(CandidateJobStatus.job_id == job_id)
        .group_by(CandidateJobStatus.status)
    ).all()
    status_counts = {status_name: count for status_name, count in status_rows}
    uploaded = int(db.scalar(select(func.count()).select_from(ResumeFile).where(ResumeFile.job_id == job_id)) or 0)
    high_match = int(
        db.scalar(
            select(func.count(distinct(CandidateMatch.candidate_id))).where(
                CandidateMatch.job_id == job_id,
                CandidateMatch.score >= 80,
            )
        )
        or 0
    )
    needs_review = int(
        db.scalar(
            select(func.count(distinct(Candidate.id)))
            .join(ResumeFile, ResumeFile.candidate_id == Candidate.id)
            .where(ResumeFile.job_id == job_id, func.json_array_length(Candidate.low_confidence_fields) > 0)
        )
        or 0
    )
    return JobFunnelStats(
        uploaded=uploaded,
        pending=int(status_counts.get("pending", 0)),
        favorite=int(status_counts.get("favorite", 0)),
        pending_contact=int(status_counts.get("pending_contact", 0)),
        rejected=int(status_counts.get("rejected", 0)),
        archived=int(status_counts.get("archived", 0)),
        high_match=high_match,
        needs_review=needs_review,
    )


@router.get("/{job_id}/jd-quality", response_model=JDQualityCheck)
def get_jd_quality(job_id: str, db: Session = Depends(get_db)) -> JDQualityCheck:
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return check_jd_quality(job)


@router.get("/{job_id}/standard-versions", response_model=list[JobStandardVersionRead])
def list_job_standard_versions(job_id: str, db: Session = Depends(get_db)) -> list[JobStandardVersionRead]:
    if not JobRepository(db).get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    rows = V2Repository(db).list_job_standard_versions(job_id)
    return [JobStandardVersionRead.model_validate(row) for row in rows]
