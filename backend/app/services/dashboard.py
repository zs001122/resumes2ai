from datetime import datetime, time, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import CandidateMatch
from app.models.resume import ResumeFile
from app.models.status import CandidateJobStatus
from app.models.v2 import CandidateDuplicateCheck, CandidateTimelineEvent, UploadProcessingTask
from app.schemas.dashboard import DashboardActivity, DashboardPayload, DashboardSummary, DashboardTodo


def build_dashboard_payload(db: Session) -> DashboardPayload:
    summary = get_dashboard_summary(db)
    return DashboardPayload(
        summary=summary,
        todos=build_dashboard_todos(summary, get_pending_duplicate_review_href(db)),
        recent_activities=get_recent_activities(db),
    )


def get_dashboard_summary(db: Session) -> DashboardSummary:
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    return DashboardSummary(
        open_jobs=count_scalar(db, select(func.count()).select_from(Job).where(Job.status == "open")),
        total_jobs=count_scalar(db, select(func.count()).select_from(Job)),
        total_candidates=count_scalar(db, select(func.count()).select_from(Candidate)),
        today_new_candidates=count_scalar(
            db,
            select(func.count()).select_from(Candidate).where(Candidate.created_at >= today_start),
        ),
        high_match_candidates=count_scalar(
            db,
            select(func.count(distinct(CandidateMatch.candidate_id))).where(CandidateMatch.score >= 80),
        ),
        pending_candidates=count_scalar(
            db,
            select(func.count()).select_from(CandidateJobStatus).where(CandidateJobStatus.status == "pending"),
        ),
        pending_contact_candidates=count_scalar(
            db,
            select(func.count()).select_from(CandidateJobStatus).where(CandidateJobStatus.status == "pending_contact"),
        ),
        parse_failed_resumes=count_scalar(
            db,
            select(func.count()).select_from(ResumeFile).where(ResumeFile.parse_status == "failed"),
        ),
        match_failed_tasks=count_scalar(
            db,
            select(func.count()).select_from(UploadProcessingTask).where(UploadProcessingTask.match_status == "failed"),
        ),
        pending_duplicate_reviews=count_scalar(
            db,
            select(func.count())
            .select_from(CandidateDuplicateCheck)
            .where(CandidateDuplicateCheck.status == "pending_review"),
        ),
    )


def build_dashboard_todos(summary: DashboardSummary, duplicate_review_href: str = "/jobs") -> list[DashboardTodo]:
    return [
        DashboardTodo(
            key="pending_duplicate_review",
            title="复核重复候选人风险",
            count=summary.pending_duplicate_reviews,
            href=duplicate_review_href,
            tone="danger" if summary.pending_duplicate_reviews else "default",
        ),
        DashboardTodo(
            key="parse_failed",
            title="处理解析失败",
            count=summary.parse_failed_resumes,
            href="/jobs",
            tone="danger" if summary.parse_failed_resumes else "default",
        ),
        DashboardTodo(
            key="match_failed",
            title="处理评分失败",
            count=summary.match_failed_tasks,
            href="/jobs",
            tone="danger" if summary.match_failed_tasks else "default",
        ),
        DashboardTodo(
            key="high_match",
            title="查看高匹配候选人",
            count=summary.high_match_candidates,
            href="/jobs",
            tone="success" if summary.high_match_candidates else "default",
        ),
        DashboardTodo(
            key="pending_contact",
            title="跟进待沟通候选人",
            count=summary.pending_contact_candidates,
            href="/jobs",
        ),
        DashboardTodo(
            key="pending",
            title="继续初筛候选人",
            count=summary.pending_candidates,
            href="/jobs",
        ),
    ]


def get_pending_duplicate_review_href(db: Session) -> str:
    row = db.scalars(
        select(CandidateDuplicateCheck)
        .where(CandidateDuplicateCheck.status == "pending_review")
        .order_by(CandidateDuplicateCheck.created_at.desc())
    ).first()
    if not row:
        return "/jobs"
    return f"/jobs/{row.job_id}/candidates/{row.candidate_id}"


def get_recent_activities(db: Session, limit: int = 10) -> list[DashboardActivity]:
    timeline_rows = list(
        db.scalars(
            select(CandidateTimelineEvent).order_by(CandidateTimelineEvent.created_at.desc()).limit(limit)
        ).all()
    )
    if timeline_rows:
        return [
            DashboardActivity(
                id=row.id,
                kind=row.action_type,
                title=row.action_summary,
                description=row.after_value or row.before_value or "候选人流程更新",
                happened_at=row.created_at,
                job_id=row.job_id,
                candidate_id=row.candidate_id,
            )
            for row in timeline_rows
        ]

    resume_rows = list(db.scalars(select(ResumeFile).order_by(ResumeFile.created_at.desc()).limit(limit)).all())
    return [
        DashboardActivity(
            id=row.id,
            kind="resume_uploaded",
            title="上传简历",
            description=row.file_name,
            happened_at=row.created_at,
            job_id=row.job_id,
            candidate_id=row.candidate_id,
        )
        for row in resume_rows
    ]


def count_scalar(db: Session, statement) -> int:
    return int(db.scalar(statement) or 0)
