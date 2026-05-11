from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.correction import FieldCorrectionLog
from app.models.resume import ResumeFieldExtraction, ResumeFile
from app.models.status import CandidateJobStatus


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_resume_file(self, resume_file_id: str) -> ResumeFile | None:
        return self.db.get(ResumeFile, resume_file_id)

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)

    def get_resume_file_for_candidate(self, job_id: str, candidate_id: str) -> ResumeFile | None:
        statement = (
            select(ResumeFile)
            .where(ResumeFile.job_id == job_id, ResumeFile.candidate_id == candidate_id)
            .order_by(ResumeFile.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def get_candidate_for_job(self, job_id: str, candidate_id: str) -> tuple[Candidate, ResumeFile] | None:
        statement = (
            select(Candidate, ResumeFile)
            .join(ResumeFile, ResumeFile.candidate_id == Candidate.id)
            .where(
                ResumeFile.job_id == job_id,
                ResumeFile.candidate_id == candidate_id,
                ResumeFile.parse_status == "success",
            )
            .order_by(ResumeFile.created_at.desc())
        )
        row = self.db.execute(statement).first()
        return (row[0], row[1]) if row else None

    def get_latest_resume_file_for_candidate(self, candidate_id: str) -> ResumeFile | None:
        statement = (
            select(ResumeFile)
            .where(ResumeFile.candidate_id == candidate_id)
            .order_by(ResumeFile.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def list_resume_files_by_job(self, job_id: str) -> list[ResumeFile]:
        statement = select(ResumeFile).where(ResumeFile.job_id == job_id).order_by(ResumeFile.created_at.desc())
        return list(self.db.scalars(statement).all())

    def list_candidates_by_job(self, job_id: str) -> list[tuple[Candidate, ResumeFile]]:
        statement = (
            select(Candidate, ResumeFile)
            .join(ResumeFile, ResumeFile.candidate_id == Candidate.id)
            .where(ResumeFile.job_id == job_id, ResumeFile.parse_status == "success")
            .order_by(ResumeFile.created_at.desc())
        )
        return list(self.db.execute(statement).all())

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

    def update_candidate(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def add_correction_logs(self, logs: list[FieldCorrectionLog]) -> list[FieldCorrectionLog]:
        for log in logs:
            self.db.add(log)
        self.db.commit()
        for log in logs:
            self.db.refresh(log)
        return logs

    def list_correction_logs(self, candidate_id: str) -> list[FieldCorrectionLog]:
        statement = (
            select(FieldCorrectionLog)
            .where(FieldCorrectionLog.candidate_id == candidate_id)
            .order_by(FieldCorrectionLog.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_candidate_status(self, job_id: str, candidate_id: str) -> CandidateJobStatus | None:
        statement = select(CandidateJobStatus).where(
            CandidateJobStatus.job_id == job_id,
            CandidateJobStatus.candidate_id == candidate_id,
        )
        return self.db.scalars(statement).first()

    def set_candidate_status(self, job_id: str, candidate_id: str, status: str) -> CandidateJobStatus:
        row = self.get_candidate_status(job_id, candidate_id)
        if row:
            row.status = status
        else:
            row = CandidateJobStatus(job_id=job_id, candidate_id=candidate_id, status=status)
            self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
