from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy import delete, func, or_, select


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.models  # noqa: F401,E402
from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.candidate import Candidate  # noqa: E402
from app.models.correction import FieldCorrectionLog  # noqa: E402
from app.models.job import Job  # noqa: E402
from app.models.match import CandidateMatch  # noqa: E402
from app.models.resume import ResumeFieldExtraction, ResumeFile  # noqa: E402
from app.models.status import CandidateJobStatus  # noqa: E402
from app.models.v2 import (  # noqa: E402
    CandidateMatchExplanation,
    CandidateNote,
    CandidateTagLink,
    CandidateTimelineEvent,
    UploadProcessingTask,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="删除指定岗位及其岗位下候选人数据")
    parser.add_argument("--job-id", required=True, help="要删除的岗位 ID")
    parser.add_argument("--yes", action="store_true", help="确认执行删除；不传时只预览")
    parser.add_argument("--keep-files", action="store_true", help="只删除数据库记录，保留上传文件")
    args = parser.parse_args()

    with SessionLocal() as db:
        job = db.get(Job, args.job_id)
        if not job:
            raise SystemExit(f"岗位不存在：{args.job_id}")

        resume_files = list(db.scalars(select(ResumeFile).where(ResumeFile.job_id == args.job_id)).all())
        resume_file_ids = [row.id for row in resume_files]
        candidate_ids = sorted({row.candidate_id for row in resume_files if row.candidate_id})
        deletable_candidate_ids, shared_candidate_ids = split_candidate_ids(db, args.job_id, candidate_ids)
        candidate_ids_to_delete = deletable_candidate_ids
        match_ids = collect_match_ids(db, args.job_id, candidate_ids_to_delete)

        file_paths = collect_file_paths(resume_files)
        summary = {
            "job": 1,
            "resume_files": len(resume_file_ids),
            "candidates_to_delete": len(candidate_ids_to_delete),
            "shared_candidates_kept": len(shared_candidate_ids),
            "candidate_matches": len(match_ids),
            "match_explanations": count_rows(
                db,
                CandidateMatchExplanation,
                CandidateMatchExplanation.match_id,
                match_ids,
            ),
            "field_extractions": count_rows(
                db,
                ResumeFieldExtraction,
                ResumeFieldExtraction.resume_file_id,
                resume_file_ids,
            ),
            "correction_logs": count_correction_logs(db, resume_file_ids, candidate_ids_to_delete),
            "upload_tasks": count_rows(db, UploadProcessingTask, UploadProcessingTask.job_id, [args.job_id]),
            "candidate_statuses": count_candidate_statuses(db, args.job_id, candidate_ids_to_delete),
            "notes": count_notes(db, args.job_id, candidate_ids_to_delete),
            "timeline_events": count_timeline_events(db, args.job_id, candidate_ids_to_delete),
            "tag_links": count_rows(db, CandidateTagLink, CandidateTagLink.candidate_id, candidate_ids_to_delete),
            "files": len(file_paths),
        }

        print(f"岗位：{job.title} ({job.id})")
        print("将删除：")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        if shared_candidate_ids:
            print("保留仍关联其他岗位的候选人：")
            for candidate_id in shared_candidate_ids:
                print(f"  {candidate_id}")

        if not args.yes:
            print("\n当前为预览模式，未删除任何数据。确认无误后追加 --yes 执行删除。")
            return

        delete_database_rows(
            db=db,
            job_id=args.job_id,
            resume_file_ids=resume_file_ids,
            candidate_ids_to_delete=candidate_ids_to_delete,
            match_ids=match_ids,
        )
        if not args.keep_files:
            delete_files(file_paths)
        print("\n删除完成。")


def split_candidate_ids(db, job_id: str, candidate_ids: list[str]) -> tuple[list[str], list[str]]:
    deletable: list[str] = []
    shared: list[str] = []
    for candidate_id in candidate_ids:
        other_count = int(
            db.scalar(
                select(func.count())
                .select_from(ResumeFile)
                .where(ResumeFile.candidate_id == candidate_id, ResumeFile.job_id != job_id)
            )
            or 0
        )
        if other_count:
            shared.append(candidate_id)
        else:
            deletable.append(candidate_id)
    return deletable, shared


def collect_match_ids(db, job_id: str, candidate_ids: list[str]) -> list[str]:
    clauses = [CandidateMatch.job_id == job_id]
    if candidate_ids:
        clauses.append(CandidateMatch.candidate_id.in_(candidate_ids))
    return list(db.scalars(select(CandidateMatch.id).where(or_(*clauses))).all())


def collect_file_paths(resume_files: list[ResumeFile]) -> list[Path]:
    paths: list[Path] = []
    for resume_file in resume_files:
        for value in [resume_file.file_path, resume_file.preview_path]:
            if value:
                paths.append((settings.upload_dir.parent / value).resolve())
    return paths


def count_rows(db, model, column, values: list[str]) -> int:
    if not values:
        return 0
    return int(db.scalar(select(func.count()).select_from(model).where(column.in_(values))) or 0)


def count_candidate_statuses(db, job_id: str, candidate_ids: list[str]) -> int:
    clauses = [CandidateJobStatus.job_id == job_id]
    if candidate_ids:
        clauses.append(CandidateJobStatus.candidate_id.in_(candidate_ids))
    return int(db.scalar(select(func.count()).select_from(CandidateJobStatus).where(or_(*clauses))) or 0)


def count_correction_logs(db, resume_file_ids: list[str], candidate_ids: list[str]) -> int:
    clauses = []
    if resume_file_ids:
        clauses.append(FieldCorrectionLog.resume_file_id.in_(resume_file_ids))
    if candidate_ids:
        clauses.append(FieldCorrectionLog.candidate_id.in_(candidate_ids))
    if not clauses:
        return 0
    return int(db.scalar(select(func.count()).select_from(FieldCorrectionLog).where(or_(*clauses))) or 0)


def count_notes(db, job_id: str, candidate_ids: list[str]) -> int:
    clauses = [CandidateNote.job_id == job_id]
    if candidate_ids:
        clauses.append(CandidateNote.candidate_id.in_(candidate_ids))
    return int(db.scalar(select(func.count()).select_from(CandidateNote).where(or_(*clauses))) or 0)


def count_timeline_events(db, job_id: str, candidate_ids: list[str]) -> int:
    clauses = [CandidateTimelineEvent.job_id == job_id]
    if candidate_ids:
        clauses.append(CandidateTimelineEvent.candidate_id.in_(candidate_ids))
    return int(db.scalar(select(func.count()).select_from(CandidateTimelineEvent).where(or_(*clauses))) or 0)


def delete_database_rows(
    db,
    job_id: str,
    resume_file_ids: list[str],
    candidate_ids_to_delete: list[str],
    match_ids: list[str],
) -> None:
    if match_ids:
        db.execute(delete(CandidateMatchExplanation).where(CandidateMatchExplanation.match_id.in_(match_ids)))
        db.execute(delete(CandidateMatch).where(CandidateMatch.id.in_(match_ids)))
    db.execute(
        delete(CandidateJobStatus).where(
            or_(
                CandidateJobStatus.job_id == job_id,
                CandidateJobStatus.candidate_id.in_(candidate_ids_to_delete),
            )
        )
    )
    db.execute(delete(UploadProcessingTask).where(UploadProcessingTask.job_id == job_id))
    db.execute(delete(CandidateNote).where(CandidateNote.job_id == job_id))
    db.execute(delete(CandidateTimelineEvent).where(CandidateTimelineEvent.job_id == job_id))

    if resume_file_ids:
        db.execute(delete(ResumeFieldExtraction).where(ResumeFieldExtraction.resume_file_id.in_(resume_file_ids)))
        db.execute(delete(FieldCorrectionLog).where(FieldCorrectionLog.resume_file_id.in_(resume_file_ids)))
    db.execute(delete(ResumeFile).where(ResumeFile.job_id == job_id))

    if candidate_ids_to_delete:
        db.execute(delete(CandidateTagLink).where(CandidateTagLink.candidate_id.in_(candidate_ids_to_delete)))
        db.execute(delete(CandidateNote).where(CandidateNote.candidate_id.in_(candidate_ids_to_delete)))
        db.execute(delete(CandidateTimelineEvent).where(CandidateTimelineEvent.candidate_id.in_(candidate_ids_to_delete)))
        db.execute(delete(FieldCorrectionLog).where(FieldCorrectionLog.candidate_id.in_(candidate_ids_to_delete)))
        db.execute(delete(Candidate).where(Candidate.id.in_(candidate_ids_to_delete)))

    db.execute(delete(Job).where(Job.id == job_id))
    db.commit()


def delete_files(paths: list[Path]) -> None:
    uploads_root = settings.upload_dir.resolve()
    for path in paths:
        if not path.exists() or uploads_root not in path.parents:
            continue
        path.unlink()
        cleanup_empty_parents(path.parent, uploads_root)


def cleanup_empty_parents(path: Path, stop_at: Path) -> None:
    current = path
    while current != stop_at and stop_at in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


if __name__ == "__main__":
    main()
