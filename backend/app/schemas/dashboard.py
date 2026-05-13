from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    open_jobs: int
    total_jobs: int
    total_candidates: int
    today_new_candidates: int
    high_match_candidates: int
    pending_candidates: int
    pending_contact_candidates: int
    parse_failed_resumes: int
    match_failed_tasks: int
    pending_duplicate_reviews: int


class DashboardActivity(BaseModel):
    id: str
    kind: str
    title: str
    description: str
    happened_at: datetime
    job_id: str | None = None
    candidate_id: str | None = None


class DashboardTodo(BaseModel):
    key: str
    title: str
    count: int
    href: str
    tone: str = "default"


class DashboardPayload(BaseModel):
    summary: DashboardSummary
    todos: list[DashboardTodo]
    recent_activities: list[DashboardActivity]
