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
        return self.set_status(job, "closed")

    def set_status(self, job: Job, status: str) -> Job:
        job.status = status
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def copy(self, job: Job) -> Job:
        copied = Job(
            title=f"{job.title} - 副本",
            department=job.department,
            location=job.location,
            salary_range=job.salary_range,
            experience_required=job.experience_required,
            education_required=job.education_required,
            jd=job.jd,
            responsibilities=job.responsibilities,
            must_have=job.must_have,
            nice_to_have=job.nice_to_have,
            deal_breakers=job.deal_breakers,
            scoring_dimensions=job.scoring_dimensions,
            status="open",
        )
        self.db.add(copied)
        self.db.commit()
        self.db.refresh(copied)
        return copied
