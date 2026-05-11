from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import CandidateMatch
from app.models.resume import ResumeFile
from app.models.status import CandidateJobStatus
from app.repositories.resumes import ResumeRepository
from app.repositories.v2 import V2Repository
from app.schemas.match import CandidateMatchRead
from app.schemas.resume import CandidateRead, CandidateStatusRead
from app.schemas.v2 import (
    CandidateJobHistoryItem,
    CandidateTagCreate,
    CandidateTagLinkRead,
    CandidateTagRead,
    CandidateTimelineEventCreate,
    TalentPoolCandidateRead,
    TalentPoolUpdate,
    TimelineActionType,
)

router = APIRouter(tags=["talent-pool"])


@router.get("/talent-pool/candidates", response_model=list[TalentPoolCandidateRead])
def list_talent_pool_candidates(
    query: str | None = None,
    skill: str | None = None,
    city: str | None = None,
    education: str | None = None,
    min_years: float | None = None,
    db: Session = Depends(get_db),
) -> list[TalentPoolCandidateRead]:
    statement = (
        select(Candidate)
        .join(CandidateJobStatus, CandidateJobStatus.candidate_id == Candidate.id)
        .where(CandidateJobStatus.status == "archived")
        .distinct()
        .order_by(Candidate.updated_at.desc())
    )
    candidates = list(db.scalars(statement).all())
    result = []
    for candidate in candidates:
        if query and query.lower() not in _candidate_search_text(candidate).lower():
            continue
        if skill and skill.lower() not in " ".join(candidate.skills or []).lower():
            continue
        if city and city not in (candidate.city or ""):
            continue
        if education and education not in (candidate.highest_education or ""):
            continue
        if min_years is not None and (candidate.years_of_experience or 0) < min_years:
            continue
        result.append(_talent_pool_candidate(db, candidate))
    return result


@router.post("/candidates/{candidate_id}/talent-pool", response_model=CandidateStatusRead)
def add_candidate_to_talent_pool(
    candidate_id: str,
    payload: TalentPoolUpdate,
    db: Session = Depends(get_db),
) -> CandidateStatusRead:
    repository = ResumeRepository(db)
    candidate = repository.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    job_id = payload.job_id or _latest_job_id_for_candidate(db, candidate_id)
    if not job_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="候选人暂无岗位关联，无法入库")
    row = repository.set_candidate_status(job_id, candidate_id, "archived")
    V2Repository(db).create_timeline_event(
        CandidateTimelineEventCreate(
            candidate_id=candidate_id,
            job_id=job_id,
            action_type=TimelineActionType.TALENT_POOL_ADDED,
            action_summary="加入人才库",
            after_value="archived",
        )
    )
    return CandidateStatusRead.model_validate(row)


@router.delete("/candidates/{candidate_id}/talent-pool", response_model=list[CandidateStatusRead])
def remove_candidate_from_talent_pool(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> list[CandidateStatusRead]:
    repository = ResumeRepository(db)
    if not repository.get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    archived_rows = list(
        db.scalars(
            select(CandidateJobStatus).where(
                CandidateJobStatus.candidate_id == candidate_id,
                CandidateJobStatus.status == "archived",
            )
        ).all()
    )
    rows = []
    for row in archived_rows:
        updated = repository.set_candidate_status(row.job_id, candidate_id, "pending")
        rows.append(updated)
        V2Repository(db).create_timeline_event(
            CandidateTimelineEventCreate(
                candidate_id=candidate_id,
                job_id=row.job_id,
                action_type=TimelineActionType.TALENT_POOL_REMOVED,
                action_summary="移出人才库",
                after_value="pending",
            )
        )
    return [CandidateStatusRead.model_validate(row) for row in rows]


@router.get("/candidates/{candidate_id}/job-history", response_model=list[CandidateJobHistoryItem])
def get_candidate_job_history(candidate_id: str, db: Session = Depends(get_db)) -> list[CandidateJobHistoryItem]:
    if not ResumeRepository(db).get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    return _job_history(db, candidate_id)


@router.get("/talent-pool/tags", response_model=list[CandidateTagRead])
def list_tags(db: Session = Depends(get_db)) -> list[CandidateTagRead]:
    return [CandidateTagRead.model_validate(row) for row in V2Repository(db).list_tags()]


@router.get("/candidates/{candidate_id}/tags", response_model=list[CandidateTagRead])
def list_candidate_tags(candidate_id: str, db: Session = Depends(get_db)) -> list[CandidateTagRead]:
    if not ResumeRepository(db).get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    return [CandidateTagRead.model_validate(row) for row in V2Repository(db).list_candidate_tags(candidate_id)]


@router.post("/candidates/{candidate_id}/tags", response_model=CandidateTagLinkRead)
def add_candidate_tag(
    candidate_id: str,
    payload: CandidateTagCreate,
    db: Session = Depends(get_db),
) -> CandidateTagLinkRead:
    if not ResumeRepository(db).get_candidate(candidate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选人不存在")
    repository = V2Repository(db)
    tag = repository.get_or_create_tag(payload)
    link = repository.add_candidate_tag(candidate_id, tag.id)
    return CandidateTagLinkRead.model_validate(link)


@router.delete("/candidates/{candidate_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_candidate_tag(candidate_id: str, tag_id: str, db: Session = Depends(get_db)) -> None:
    V2Repository(db).remove_candidate_tag(candidate_id, tag_id)


def _talent_pool_candidate(db: Session, candidate: Candidate) -> TalentPoolCandidateRead:
    repository = V2Repository(db)
    latest_match = db.scalars(
        select(CandidateMatch)
        .where(CandidateMatch.candidate_id == candidate.id)
        .order_by(CandidateMatch.created_at.desc())
    ).first()
    return TalentPoolCandidateRead(
        candidate=CandidateRead.model_validate(candidate),
        tags=[CandidateTagRead.model_validate(row) for row in repository.list_candidate_tags(candidate.id)],
        job_history=_job_history(db, candidate.id),
        latest_match=CandidateMatchRead.model_validate(latest_match) if latest_match else None,
    )


def _job_history(db: Session, candidate_id: str) -> list[CandidateJobHistoryItem]:
    rows = db.execute(
        select(Job, CandidateJobStatus)
        .join(CandidateJobStatus, CandidateJobStatus.job_id == Job.id)
        .where(CandidateJobStatus.candidate_id == candidate_id)
        .order_by(CandidateJobStatus.updated_at.desc())
    ).all()
    return [
        CandidateJobHistoryItem(
            job_id=job.id,
            job_title=job.title,
            job_status=job.status,
            candidate_status=status_row.status,
            updated_at=status_row.updated_at,
        )
        for job, status_row in rows
    ]


def _latest_job_id_for_candidate(db: Session, candidate_id: str) -> str | None:
    row = db.scalars(
        select(ResumeFile)
        .where(ResumeFile.candidate_id == candidate_id)
        .order_by(ResumeFile.created_at.desc())
    ).first()
    return row.job_id if row else None


def _candidate_search_text(candidate: Candidate) -> str:
    return " ".join(
        [
            candidate.name or "",
            candidate.phone or "",
            candidate.email or "",
            candidate.city or "",
            candidate.current_company or "",
            candidate.current_title or "",
            candidate.highest_education or "",
            " ".join(candidate.skills or []),
        ]
    )
