from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.jobs import JobRepository
from app.repositories.matches import CandidateMatchRepository
from app.repositories.resumes import ResumeRepository
from app.schemas.match import CandidateMatchRead
from app.services.matching import generate_candidate_match

router = APIRouter(prefix="/jobs/{job_id}/candidates/{candidate_id}/match", tags=["matches"])


@router.post("", response_model=CandidateMatchRead)
async def create_candidate_match(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateMatchRead:
    job = JobRepository(db).get(job_id)
    candidate = ResumeRepository(db).get_candidate(candidate_id)
    if not job or not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")

    payload = await generate_candidate_match(job, candidate)
    row = CandidateMatchRepository(db).create(job_id, candidate_id, payload)
    return CandidateMatchRead.model_validate(row)


@router.get("", response_model=CandidateMatchRead)
def get_candidate_match(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateMatchRead:
    row = CandidateMatchRepository(db).latest(job_id, candidate_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配结果不存在")
    return CandidateMatchRead.model_validate(row)
