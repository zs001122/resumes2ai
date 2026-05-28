from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.matching import _fallback_match
from app.services.parsers.resume_text import ResumeTextExtractor
from app.services.resume_parser import parse_resume_text


JOB_PROFILES = {
    "software-intern": SimpleNamespace(
        title="软件开发实习生",
        department="研发中心",
        location="广州",
        experience_required="应届生或 1 年以内实习经验",
        education_required="本科及以上",
        responsibilities=["参与内部业务系统开发", "接口联调", "基础测试"],
        must_have=["Python", "React", "SQL"],
        nice_to_have=["FastAPI", "Docker"],
        deal_breakers=["完全没有项目经验"],
        scoring_dimensions=["技术栈匹配", "项目经历", "沟通表达"],
    ),
    "data-developer": SimpleNamespace(
        title="数据开发工程师",
        department="数据中心",
        location="广州",
        experience_required="2 年以上数据开发经验",
        education_required="专科及以上",
        responsibilities=["数据清洗", "ETL 开发", "数据仓库建模", "SQL 优化"],
        must_have=["SQL", "ETL", "MySQL"],
        nice_to_have=["Python", "数据仓库", "Linux"],
        deal_breakers=["完全没有 SQL 经验"],
        scoring_dimensions=["数据开发经验", "ETL 项目", "SQL 能力"],
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-dir", required=True)
    parser.add_argument("--job-profile", choices=sorted(JOB_PROFILES), default="software-intern")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = diagnose(Path(args.sample_dir), JOB_PROFILES[args.job_profile])
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return
    for row in rows:
        if row.get("error"):
            print(f"{row['file']}: ERROR {row['error']} {row.get('message', '')}")
            continue
        print(
            f"{row['file']}: name={row['name']} years={row['years']}({row.get('years_source')}) edu={row['education_count']} "
            f"work={row['work_count']} project={row['project_count']} score={row['match_score']} {row['match_level']}"
        )


def diagnose(sample_dir: Path, job: Any) -> list[dict[str, Any]]:
    extractor = ResumeTextExtractor()
    rows = []
    for path in sorted(sample_dir.iterdir()):
        if path.suffix.lower() not in {".doc", ".docx", ".pdf", ".txt"}:
            continue
        row: dict[str, Any] = {"file": path.name, "suffix": path.suffix.lower()}
        try:
            text = extractor.extract_text(path)
            parsed = parse_resume_text(path.name, text)
            data = parsed.candidate_data
            years_source = next(
                (item for item in parsed.field_sources if item.get("field_name") == "years_of_experience"),
                {},
            )
            match = _fallback_match(job, SimpleNamespace(**data), "diagnostic-local-fallback")
            row.update(
                {
                    "text_len": len(text),
                    "name": data.get("name"),
                    "years": data.get("years_of_experience"),
                    "years_source": years_source.get("source_text"),
                    "years_confidence": years_source.get("confidence"),
                    "highest_education": data.get("highest_education"),
                    "education_count": len(data.get("education") or []),
                    "work_count": len(data.get("work_experiences") or []),
                    "project_count": len(data.get("project_experiences") or []),
                    "skills": data.get("skills"),
                    "low_confidence": data.get("low_confidence_fields"),
                    "match_score": match.score,
                    "match_level": match.level,
                    "matched_points": match.matched_points,
                    "weak_points": match.weak_points,
                    "first_education": (data.get("education") or [None])[0],
                    "first_work": (data.get("work_experiences") or [None])[0],
                    "first_project": (data.get("project_experiences") or [None])[0],
                }
            )
        except Exception as exc:
            row.update({"error": type(exc).__name__, "message": str(exc)})
        rows.append(row)
    return rows


if __name__ == "__main__":
    main()
