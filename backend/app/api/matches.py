from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.jobs import JobRepository
from app.repositories.matches import CandidateMatchRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.v2 import V2Repository
from app.schemas.match import CandidateMatchRead, CandidateRecommendationReport
from app.schemas.v2 import CandidateMatchExplanationRead
from app.services.match_explanations import build_match_explanations
from app.services.matching import generate_candidate_match
from app.services.recommendation_report import build_recommendation_markdown

router = APIRouter(prefix="/jobs/{job_id}/candidates/{candidate_id}/match", tags=["matches"])


@router.post("", response_model=CandidateMatchRead)
async def create_candidate_match(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateMatchRead:
    job = JobRepository(db).get(job_id)
    candidate_row = ResumeRepository(db).get_candidate_for_job(job_id, candidate_id)
    if not job or not candidate_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")

    candidate, _resume_file = candidate_row
    payload = await generate_candidate_match(job, candidate)
    v2_repository = V2Repository(db)
    version = v2_repository.get_latest_job_standard_version(job_id)
    row = CandidateMatchRepository(db).create(
        job_id,
        candidate_id,
        payload,
        job_standard_version_id=version.id if version else None,
    )
    v2_repository.replace_match_explanations(row.id, build_match_explanations(row, candidate))
    return CandidateMatchRead.model_validate(row)


@router.get("", response_model=CandidateMatchRead)
def get_candidate_match(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateMatchRead:
    if not ResumeRepository(db).get_candidate_for_job(job_id, candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    row = CandidateMatchRepository(db).latest(job_id, candidate_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配结果不存在")
    return CandidateMatchRead.model_validate(row)


@router.get("/explanations", response_model=list[CandidateMatchExplanationRead])
def get_candidate_match_explanations(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> list[CandidateMatchExplanationRead]:
    repository = ResumeRepository(db)
    candidate_row = repository.get_candidate_for_job(job_id, candidate_id)
    if not candidate_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")
    row = CandidateMatchRepository(db).latest(job_id, candidate_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配结果不存在")
    explanations = V2Repository(db).list_match_explanations(row.id)
    if not explanations:
        candidate, _resume_file = candidate_row
        explanations = V2Repository(db).replace_match_explanations(row.id, build_match_explanations(row, candidate))
    return [CandidateMatchExplanationRead.model_validate(item) for item in explanations]


@router.get("/recommendation-report", response_model=CandidateRecommendationReport)
def get_candidate_recommendation_report(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateRecommendationReport:
    job = JobRepository(db).get(job_id)
    repository = ResumeRepository(db)
    candidate_row = repository.get_candidate_for_job(job_id, candidate_id)
    if not job or not candidate_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位或候选人不存在")

    match = CandidateMatchRepository(db).latest(job_id, candidate_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配结果不存在，请先生成评分")
    candidate, _resume_file = candidate_row
    v2_repository = V2Repository(db)
    explanations = v2_repository.list_match_explanations(match.id)
    if not explanations:
        explanations = v2_repository.replace_match_explanations(match.id, build_match_explanations(match, candidate))
    return CandidateRecommendationReport(
        candidate_id=candidate_id,
        job_id=job_id,
        content=build_recommendation_markdown(job, candidate, match, explanations),
    )
