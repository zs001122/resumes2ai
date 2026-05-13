from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardActivity, DashboardPayload, DashboardSummary, DashboardTodo
from app.services.dashboard import (
    build_dashboard_payload,
    build_dashboard_todos,
    get_dashboard_summary,
    get_pending_duplicate_review_href,
    get_recent_activities,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardPayload)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardPayload:
    return build_dashboard_payload(db)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    return get_dashboard_summary(db)


@router.get("/todos", response_model=list[DashboardTodo])
def get_todos(db: Session = Depends(get_db)) -> list[DashboardTodo]:
    return build_dashboard_todos(get_dashboard_summary(db), get_pending_duplicate_review_href(db))


@router.get("/recent-activities", response_model=list[DashboardActivity])
def get_activities(db: Session = Depends(get_db)) -> list[DashboardActivity]:
    return get_recent_activities(db)
