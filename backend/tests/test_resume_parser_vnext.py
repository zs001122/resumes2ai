import json
from pathlib import Path

import pytest

import app.services.resume_parser as resume_parser
import app.services.resume_parser_vnext as resume_parser_vnext
from app.services.resume_parser_vnext import parse_resume_text_vnext

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "resume_parse_vnext"
PROMPT_DIR = Path(__file__).parents[1] / "app" / "services" / "resume_parse_prompts"
PROMPT_FILES = ["basics.jinja", "work.jinja", "education.jinja", "skills.jinja", "projects.jinja"]


def _fixture_cases():
    return sorted(path.stem for path in FIXTURE_DIR.glob("*.txt"))


@pytest.mark.parametrize("case_name", _fixture_cases())
@pytest.mark.anyio
async def test_resume_parser_vnext_section_candidates(case_name, monkeypatch):
    monkeypatch.setattr(resume_parser.settings, "ai_resume_parse_enabled", False)
    monkeypatch.setattr(resume_parser_vnext.settings, "ai_resume_parse_enabled", False)

    resume_text = (FIXTURE_DIR / f"{case_name}.txt").read_text(encoding="utf-8")
    expected = json.loads((FIXTURE_DIR / f"{case_name}.expected.json").read_text(encoding="utf-8"))

    parsed = await parse_resume_text_vnext(expected["file_name"], resume_text)
    candidate = parsed.parsed_resume.candidate_data

    assert parsed.parser_version == "resume-parser-vnext-0.2"
    assert parsed.blocks
    assert parsed.field_candidates
    assert parsed.quality_score >= 45

    for field_name in ["name", "phone", "email", "city", "years_of_experience"]:
        if field_name in expected:
            assert candidate[field_name] == expected[field_name]

    for skill in expected.get("skills_any", []):
        assert skill in candidate["skills"]

    assert len(candidate["education"]) == expected["education_count"]
    assert len(candidate["work_experiences"]) == expected["work_count"]
    assert len(candidate["project_experiences"]) == expected["project_count"]

    low_confidence_fields = set(candidate["low_confidence_fields"])
    for field_name in expected.get("low_confidence_present", []):
        assert field_name in low_confidence_fields
    for field_name in expected.get("low_confidence_absent", []):
        assert field_name not in low_confidence_fields

    extractors = {candidate.extractor for candidate in parsed.field_candidates}
    for extractor in expected["required_candidate_extractors"]:
        assert extractor in extractors

    selected_section_fields = {
        candidate.field_name
        for candidate in parsed.field_candidates
        if candidate.extractor.startswith("section:") and candidate.selected
    }
    assert "name" in selected_section_fields
    assert "education" in selected_section_fields
    assert "project_experiences" in selected_section_fields

    if expected.get("work_count", 0):
        assert "work_experiences" in selected_section_fields
    else:
        missing_work = [
            candidate
            for candidate in parsed.field_candidates
            if candidate.field_name == "work_experiences" and not candidate.selected
        ]
        assert missing_work
        assert any(candidate.rejection_reason == "missing_required_field" for candidate in missing_work)


def test_resume_parse_prompt_templates_are_present():
    for file_name in PROMPT_FILES:
        path = PROMPT_DIR / file_name
        assert path.exists(), file_name
        content = path.read_text(encoding="utf-8")
        assert "{{ section_text }}" in content
        assert "JSON" in content
