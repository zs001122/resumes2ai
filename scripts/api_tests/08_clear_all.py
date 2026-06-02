from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from sqlalchemy import delete, func, select


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
    CandidateDuplicateCheck,
    CandidateMatchExplanation,
    CandidateNote,
    CandidateTag,
    CandidateTagLink,
    CandidateTimelineEvent,
    JobStandardVersion,
    UploadProcessingTask,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="全量清空所有岗位、候选人、上传记录与上传文件")
    parser.add_argument("--yes", action="store_true", help="确认执行清空；不传时只预览")
    parser.add_argument("--keep-files", action="store_true", help="只清空数据库记录，保留 uploads 目录文件")
    args = parser.parse_args()

    with SessionLocal() as db:
        summary = {
            "jobs": count_rows(db, Job),
            "resume_files": count_rows(db, ResumeFile),
            "candidates": count_rows(db, Candidate),
            "candidate_matches": count_rows(db, CandidateMatch),
            "match_explanations": count_rows(db, CandidateMatchExplanation),
            "field_extractions": count_rows(db, ResumeFieldExtraction),
            "correction_logs": count_rows(db, FieldCorrectionLog),
            "candidate_statuses": count_rows(db, CandidateJobStatus),
            "upload_tasks": count_rows(db, UploadProcessingTask),
            "notes": count_rows(db, CandidateNote),
            "timeline_events": count_rows(db, CandidateTimelineEvent),
            "duplicate_checks": count_rows(db, CandidateDuplicateCheck),
            "job_standard_versions": count_rows(db, JobStandardVersion),
            "candidate_tags": count_rows(db, CandidateTag),
            "tag_links": count_rows(db, CandidateTagLink),
            "files": count_upload_files(),
        }

        print("将全量清空：")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print(f"  uploads_dir: {settings.upload_dir.resolve()}")

        if not args.yes:
            print("\n当前为预览模式，未删除任何数据。确认无误后追加 --yes 执行清空。")
            return

        clear_database(db)
        if args.keep_files:
            print("\n数据库记录已清空，uploads 目录文件已保留。")
        else:
            deleted_files = clear_upload_dir()
            print(f"\n数据库记录已清空，uploads 目录文件已删除：{deleted_files} 个文件。")


def count_rows(db, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def count_upload_files() -> int:
    upload_root = settings.upload_dir.resolve()
    if not upload_root.exists():
        return 0
    return sum(1 for path in upload_root.rglob("*") if path.is_file())


def clear_database(db) -> None:
    db.execute(delete(CandidateMatchExplanation))
    db.execute(delete(CandidateDuplicateCheck))
    db.execute(delete(CandidateTagLink))
    db.execute(delete(CandidateJobStatus))
    db.execute(delete(UploadProcessingTask))
    db.execute(delete(CandidateNote))
    db.execute(delete(CandidateTimelineEvent))
    db.execute(delete(ResumeFieldExtraction))
    db.execute(delete(FieldCorrectionLog))
    db.execute(delete(CandidateMatch))
    db.execute(delete(ResumeFile))
    db.execute(delete(JobStandardVersion))
    db.execute(delete(Candidate))
    db.execute(delete(Job))
    db.execute(delete(CandidateTag))
    db.commit()


def clear_upload_dir() -> int:
    upload_root = settings.upload_dir.resolve()
    if not upload_root.exists():
        return 0
    ensure_safe_upload_dir(upload_root)

    file_count = sum(1 for path in upload_root.rglob("*") if path.is_file())
    shutil.rmtree(upload_root)
    upload_root.mkdir(parents=True, exist_ok=True)
    (upload_root / "resumes").mkdir(parents=True, exist_ok=True)
    # Restore .gitkeep so the uploads directory stays tracked.
    (upload_root / ".gitkeep").write_text("", encoding="utf-8")
    return file_count


def ensure_safe_upload_dir(upload_root: Path) -> None:
    backend_root = BACKEND_ROOT.resolve()
    if upload_root == backend_root or upload_root == PROJECT_ROOT.resolve() or upload_root == Path(upload_root.anchor):
        raise RuntimeError(f"拒绝清空危险 uploads 路径：{upload_root}")
    try:
        upload_root.relative_to(backend_root)
    except ValueError as exc:
        raise RuntimeError(f"uploads 路径不在 backend 目录下，已拒绝删除：{upload_root}") from exc


if __name__ == "__main__":
    main()
