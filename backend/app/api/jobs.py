from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.jobs import JobRepository
from app.schemas.job import JDParseRequest, JDParseResult, JobCreate, JobListItem, JobRead, JobUpdate
from app.services.jobs import parse_jd_locally

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
    return JobRead.model_validate(repository.update(job, payload))


@router.post("/{job_id}/close", response_model=JobRead)
def close_job(job_id: str, db: Session = Depends(get_db)) -> JobRead:
    repository = JobRepository(db)
    job = repository.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return JobRead.model_validate(repository.close(job))
