from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.resume import ResumeFieldExtraction, ResumeFile


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_resume_file(self, resume_file_id: str) -> ResumeFile | None:
        return self.db.get(ResumeFile, resume_file_id)

    def list_resume_files_by_job(self, job_id: str) -> list[ResumeFile]:
        statement = select(ResumeFile).where(ResumeFile.job_id == job_id).order_by(ResumeFile.created_at.desc())
        return list(self.db.scalars(statement).all())

    def create_resume_file(self, resume_file: ResumeFile) -> ResumeFile:
        self.db.add(resume_file)
        self.db.commit()
        self.db.refresh(resume_file)
        return resume_file

    def create_candidate(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def update_resume_file(self, resume_file: ResumeFile) -> ResumeFile:
        self.db.add(resume_file)
        self.db.commit()
        self.db.refresh(resume_file)
        return resume_file

    def replace_field_extractions(
        self,
        resume_file_id: str,
        field_extractions: list[ResumeFieldExtraction],
    ) -> list[ResumeFieldExtraction]:
        old_rows = self.db.scalars(
            select(ResumeFieldExtraction).where(ResumeFieldExtraction.resume_file_id == resume_file_id)
        ).all()
        for row in old_rows:
            self.db.delete(row)
        for row in field_extractions:
            self.db.add(row)
        self.db.commit()
        for row in field_extractions:
            self.db.refresh(row)
        return field_extractions

    def list_field_extractions(self, resume_file_id: str) -> list[ResumeFieldExtraction]:
        statement = select(ResumeFieldExtraction).where(ResumeFieldExtraction.resume_file_id == resume_file_id)
        return list(self.db.scalars(statement).all())
