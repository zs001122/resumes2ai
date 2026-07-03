#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.services.resume_parser as resume_parser
import app.services.resume_parser_vnext as resume_parser_vnext
from app.services.parsers.resume_text import ResumeTextExtractor
from app.services.resume_parser_vnext import parse_resume_text_vnext


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a resume_parse_vnext fixture from a real resume file.")
    parser.add_argument("--input", required=True, type=Path, help="Resume file path: PDF, DOCX, or TXT.")
    parser.add_argument("--case-name", required=True, help="Fixture case name, without extension.")
    parser.add_argument("--file-name", help="Logical resume file name passed into parser. Defaults to input file name.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BACKEND_ROOT / "tests" / "fixtures" / "resume_parse_vnext",
        help="Fixture output directory.",
    )
    parser.add_argument(
        "--raw-exclude",
        action="append",
        default=[],
        help="Text that must not appear in joined project raw. Can be repeated.",
    )
    parser.add_argument(
        "--low-confidence-absent",
        action="append",
        default=[],
        help="Field expected to be absent from low_confidence_fields. Can be repeated.",
    )
    return parser.parse_args()


async def build_fixture(args: argparse.Namespace) -> dict[str, Any]:
    resume_parser.settings.ai_resume_parse_enabled = False
    resume_parser_vnext.settings.ai_resume_parse_enabled = False

    input_path = args.input.resolve()
    text = ResumeTextExtractor().extract_text(input_path)
    file_name = args.file_name or input_path.name
    parsed = await parse_resume_text_vnext(file_name, text)
    candidate = parsed.parsed_resume.candidate_data
    expected = {
        "file_name": file_name,
        "name": candidate.get("name"),
        "phone": candidate.get("phone"),
        "email": candidate.get("email"),
        "city": candidate.get("city"),
        "years_of_experience": candidate.get("years_of_experience"),
        "education_count": len(candidate.get("education") or []),
        "work_count": len(candidate.get("work_experiences") or []),
        "project_count": len(candidate.get("project_experiences") or []),
        "low_confidence_absent": sorted(set(args.low_confidence_absent)),
        "required_candidate_extractors": sorted(
            {
                item.extractor
                for item in parsed.field_candidates
                if item.extractor.startswith("section:") and item.selected
            }
        ),
    }
    if args.raw_exclude:
        expected["project_raw_excludes"] = args.raw_exclude
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / f"{args.case_name}.txt").write_text(text, encoding="utf-8")
    (args.output_dir / f"{args.case_name}.expected.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return expected


def main() -> None:
    args = parse_args()
    expected = asyncio.run(build_fixture(args))
    print(json.dumps(expected, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
