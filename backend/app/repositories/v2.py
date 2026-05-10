from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.v2 import (
    CandidateMatchExplanation,
    CandidateNote,
    CandidateTag,
    CandidateTagLink,
    CandidateTimelineEvent,
    UploadProcessingTask,
)
from app.schemas.v2 import (
    CandidateMatchExplanationCreate,
    CandidateNoteCreate,
    CandidateTagCreate,
    CandidateTimelineEventCreate,
    UploadProcessingTaskCreate,
    UploadProcessingTaskUpdate,
)


class V2Repository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_upload_task(self, payload: UploadProcessingTaskCreate) -> UploadProcessingTask:
        row = UploadProcessingTask(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_upload_task(self, task_id: str) -> UploadProcessingTask | None:
        return self.db.get(UploadProcessingTask, task_id)

    def list_upload_tasks(self, job_id: str) -> list[UploadProcessingTask]:
        statement = (
            select(UploadProcessingTask)
            .where(UploadProcessingTask.job_id == job_id)
            .order_by(UploadProcessingTask.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_failed_upload_tasks(self, job_id: str) -> list[UploadProcessingTask]:
        statement = (
            select(UploadProcessingTask)
            .where(
                UploadProcessingTask.job_id == job_id,
                (UploadProcessingTask.parse_status == "failed") | (UploadProcessingTask.match_status == "failed"),
            )
            .order_by(UploadProcessingTask.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_upload_task_for_resume_file(self, resume_file_id: str) -> UploadProcessingTask | None:
        statement = select(UploadProcessingTask).where(UploadProcessingTask.resume_file_id == resume_file_id)
        return self.db.scalars(statement).first()

    def update_upload_task(
        self,
        task: UploadProcessingTask,
        payload: UploadProcessingTaskUpdate,
    ) -> UploadProcessingTask:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def increment_upload_task_retry(self, task: UploadProcessingTask) -> UploadProcessingTask:
        task.retry_count += 1
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def replace_match_explanations(
        self,
        match_id: str,
        payloads: list[CandidateMatchExplanationCreate],
    ) -> list[CandidateMatchExplanation]:
        old_rows = self.db.scalars(
            select(CandidateMatchExplanation).where(CandidateMatchExplanation.match_id == match_id)
        ).all()
        for row in old_rows:
            self.db.delete(row)
        rows = [CandidateMatchExplanation(match_id=match_id, **payload.model_dump()) for payload in payloads]
        for row in rows:
            self.db.add(row)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows

    def list_match_explanations(self, match_id: str) -> list[CandidateMatchExplanation]:
        statement = (
            select(CandidateMatchExplanation)
            .where(CandidateMatchExplanation.match_id == match_id)
            .order_by(CandidateMatchExplanation.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def create_note(self, payload: CandidateNoteCreate) -> CandidateNote:
        row = CandidateNote(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_notes(self, candidate_id: str, job_id: str | None = None) -> list[CandidateNote]:
        statement = select(CandidateNote).where(CandidateNote.candidate_id == candidate_id)
        if job_id is not None:
            statement = statement.where(CandidateNote.job_id == job_id)
        statement = statement.order_by(CandidateNote.created_at.desc())
        return list(self.db.scalars(statement).all())

    def create_timeline_event(self, payload: CandidateTimelineEventCreate) -> CandidateTimelineEvent:
        data = payload.model_dump()
        data["action_type"] = str(data["action_type"])
        row = CandidateTimelineEvent(**data)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_timeline_events(self, candidate_id: str, job_id: str | None = None) -> list[CandidateTimelineEvent]:
        statement = select(CandidateTimelineEvent).where(CandidateTimelineEvent.candidate_id == candidate_id)
        if job_id is not None:
            statement = statement.where(CandidateTimelineEvent.job_id == job_id)
        statement = statement.order_by(CandidateTimelineEvent.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_or_create_tag(self, payload: CandidateTagCreate) -> CandidateTag:
        name = payload.name.strip()
        existing = self.db.scalars(select(CandidateTag).where(CandidateTag.name == name)).first()
        if existing:
            return existing
        row = CandidateTag(name=name)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_tags(self) -> list[CandidateTag]:
        statement = select(CandidateTag).order_by(CandidateTag.name.asc())
        return list(self.db.scalars(statement).all())

    def add_candidate_tag(self, candidate_id: str, tag_id: str) -> CandidateTagLink:
        existing = self.db.scalars(
            select(CandidateTagLink).where(
                CandidateTagLink.candidate_id == candidate_id,
                CandidateTagLink.tag_id == tag_id,
            )
        ).first()
        if existing:
            return existing
        row = CandidateTagLink(candidate_id=candidate_id, tag_id=tag_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def remove_candidate_tag(self, candidate_id: str, tag_id: str) -> None:
        row = self.db.scalars(
            select(CandidateTagLink).where(
                CandidateTagLink.candidate_id == candidate_id,
                CandidateTagLink.tag_id == tag_id,
            )
        ).first()
        if row:
            self.db.delete(row)
            self.db.commit()

    def list_candidate_tags(self, candidate_id: str) -> list[CandidateTag]:
        statement = (
            select(CandidateTag)
            .join(CandidateTagLink, CandidateTagLink.tag_id == CandidateTag.id)
            .where(CandidateTagLink.candidate_id == candidate_id)
            .order_by(CandidateTag.name.asc())
        )
        return list(self.db.scalars(statement).all())
