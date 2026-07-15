#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


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
    parser.add_argument(
        "--redact",
        action="store_true",
        help="Redact detected name, phone, and email before writing fixture files.",
    )
    parser.add_argument("--redact-name", default="张三", help="Name replacement used with --redact.")
    parser.add_argument("--redact-phone", default="13800000000", help="Phone replacement used with --redact.")
    parser.add_argument("--redact-email", default="candidate@example.com", help="Email replacement used with --redact.")
    return parser.parse_args()


PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d(?:[-\s]?\d{4}){2}(?!\d)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _redact_resume_text(
    text: str,
    candidate_data: dict[str, Any],
    *,
    name_alias: str,
    phone_alias: str,
    email_alias: str,
) -> str:
    redacted = text
    redacted = _replace_detected_value(redacted, candidate_data.get("name"), name_alias)
    redacted = _replace_detected_value(redacted, candidate_data.get("phone"), phone_alias)
    redacted = _replace_detected_value(redacted, candidate_data.get("email"), email_alias)
    redacted = PHONE_PATTERN.sub(phone_alias, redacted)
    redacted = EMAIL_PATTERN.sub(email_alias, redacted)
    return redacted


def _redact_file_name(
    file_name: str,
    candidate_data: dict[str, Any],
    *,
    name_alias: str,
    phone_alias: str,
    email_alias: str,
) -> str:
    redacted = file_name
    redacted = _replace_detected_value(redacted, candidate_data.get("name"), name_alias)
    redacted = _replace_detected_value(redacted, candidate_data.get("phone"), phone_alias)
    redacted = _replace_detected_value(redacted, candidate_data.get("email"), email_alias)
    return PHONE_PATTERN.sub(phone_alias, redacted)


def _replace_detected_value(text: str, value: Any, replacement: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return text
    return text.replace(value.strip(), replacement)


async def build_fixture(args: argparse.Namespace) -> dict[str, Any]:
    import app.services.resume_parser as resume_parser
    import app.services.resume_parser_vnext as resume_parser_vnext
    from app.services.parsers.resume_text import ResumeTextExtractor
    from app.services.resume_parser_vnext import parse_resume_text_vnext

    resume_parser.settings.ai_resume_parse_enabled = False
    resume_parser_vnext.settings.ai_resume_parse_enabled = False

    input_path = args.input.resolve()
    extractor = ResumeTextExtractor()
    text = extractor.extract_text(input_path)
    file_name = args.file_name or input_path.name
    redaction_candidate: dict[str, Any] | None = None

    if args.redact:
        original = await parse_resume_text_vnext(file_name, text)
        original_candidate = original.parsed_resume.candidate_data
        redaction_candidate = original_candidate
        text = _redact_resume_text(
            text,
            original_candidate,
            name_alias=args.redact_name,
            phone_alias=args.redact_phone,
            email_alias=args.redact_email,
        )
        file_name = _redact_file_name(
            file_name,
            original_candidate,
            name_alias=args.redact_name,
            phone_alias=args.redact_phone,
            email_alias=args.redact_email,
        )

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
    raw_excludes = args.raw_exclude
    if args.redact and redaction_candidate:
        raw_excludes = [
            _redact_resume_text(
                item,
                redaction_candidate,
                name_alias=args.redact_name,
                phone_alias=args.redact_phone,
                email_alias=args.redact_email,
            )
            for item in raw_excludes
        ]
    if raw_excludes:
        expected["project_raw_excludes"] = raw_excludes
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
