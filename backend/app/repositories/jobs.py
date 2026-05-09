from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, status: str | None = None) -> list[Job]:
        statement = select(Job).order_by(Job.created_at.desc())
        if status:
            statement = statement.where(Job.status == status)
        return list(self.db.scalars(statement).all())

    def get(self, job_id: str) -> Job | None:
        return self.db.get(Job, job_id)

    def create(self, payload: JobCreate) -> Job:
        job = Job(**payload.model_dump())
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update(self, job: Job, payload: JobUpdate) -> Job:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(job, key, value)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def close(self, job: Job) -> Job:
        job.status = "closed"
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
