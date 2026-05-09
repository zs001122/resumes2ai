from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import CandidateMatch
from app.schemas.match import CandidateMatchCreate


class CandidateMatchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest(self, job_id: str, candidate_id: str) -> CandidateMatch | None:
        statement = (
            select(CandidateMatch)
            .where(CandidateMatch.job_id == job_id, CandidateMatch.candidate_id == candidate_id)
            .order_by(CandidateMatch.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def create(self, job_id: str, candidate_id: str, payload: CandidateMatchCreate) -> CandidateMatch:
        row = CandidateMatch(job_id=job_id, candidate_id=candidate_id, **payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
