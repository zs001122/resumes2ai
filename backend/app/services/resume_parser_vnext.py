from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.services.resume_parser import ParsedResume, parse_resume_text_with_ai
from app.services.resume_sections import normalized_lines, section_blocks

PARSER_VERSION = "resume-parser-vnext-0.4"

BASIC_FIELDS = [
    "name",
    "phone",
    "email",
    "city",
    "years_of_experience",
    "highest_education",
    "current_company",
    "current_title",
]
SECTION_FIELD_SOURCES = {
    "skills": "skills",
    "education": "education",
    "work_experiences": "work",
    "project_experiences": "project",
}
ITEM_LEVEL_FIELDS = {"work_experiences", "project_experiences"}
LOW_CONFIDENCE_WEIGHTS = {
    "name": 10,
    "education": 10,
    "phone": 6,
    "email": 6,
    "highest_education": 6,
    "work_experiences": 5,
    "project_experiences": 5,
    "years_of_experience": 4,
    "current_title": 3,
    "city": 2,
}
LOW_CONFIDENCE_EXTRACTOR = {
    "name": "section:basics:rules",
    "phone": "section:basics:rules",
    "email": "section:basics:rules",
    "city": "section:basics:rules",
    "years_of_experience": "section:basics:rules",
    "highest_education": "section:education:rules",
    "current_company": "section:work:rules",
    "current_title": "section:work:rules",
    "education": "section:education:rules",
    "work_experiences": "section:work:rules",
    "project_experiences": "section:projects:rules",
    "skills": "section:skills:rules",
}


@dataclass(frozen=True)
class TextDocument:
    file_name: str
    text: str
    source: str
    lines: list[str]


@dataclass(frozen=True)
class ResumeBlockRecord:
    block_type: str
    title: str | None
    text: str
    start_offset: int | None
    end_offset: int | None
    confidence: float
    inferred: bool


@dataclass(frozen=True)
class FieldCandidateRecord:
    field_name: str
    value_json: Any
    source_text: str | None
    extractor: str
    confidence: float | None
    selected: bool
    rejection_reason: str | None = None


@dataclass(frozen=True)
class ParsedResumeVNext:
    parsed_resume: ParsedResume
    document: TextDocument
    blocks: list[ResumeBlockRecord]
    field_candidates: list[FieldCandidateRecord]
    parser_version: str
    ai_enabled: bool
    quality_score: float
    warnings: list[str]


async def parse_resume_text_vnext(file_name: str, text: str) -> ParsedResumeVNext:
    document = _build_document(file_name, text)
    parsed_resume = await parse_resume_text_with_ai(file_name, text)
    blocks = _build_blocks(document)
    field_candidates = _build_field_candidates(parsed_resume, blocks, document)
    warnings = _quality_warnings(parsed_resume, blocks)
    quality_score = _quality_score(parsed_resume, blocks, field_candidates)
    return ParsedResumeVNext(
        parsed_resume=parsed_resume,
        document=document,
        blocks=blocks,
        field_candidates=field_candidates,
        parser_version=PARSER_VERSION,
        ai_enabled=settings.ai_resume_parse_enabled,
        quality_score=quality_score,
        warnings=warnings,
    )


def _build_document(file_name: str, text: str) -> TextDocument:
    source = f"{file_name}\n{text}"
    return TextDocument(
        file_name=file_name,
        text=text,
        source=source,
        lines=normalized_lines(source),
    )


def _build_blocks(document: TextDocument) -> list[ResumeBlockRecord]:
    records: list[ResumeBlockRecord] = []
    for section in section_blocks(document.lines):
        block_text = "\n".join(section.lines)
        start, end = _locate_span(document.source, section.lines[0] if section.lines else block_text)
        if start is not None and end is not None and len(block_text) > len(section.lines[0]):
            end = min(len(document.source), start + len(block_text))
        records.append(
            ResumeBlockRecord(
                block_type=section.key,
                title=section.title,
                text=block_text,
                start_offset=start,
                end_offset=end,
                confidence=section.confidence,
                inferred=section.inferred,
            )
        )
    if not records and document.lines:
        preview = "\n".join(document.lines[:12])
        start, end = _locate_span(document.source, document.lines[0])
        records.append(
            ResumeBlockRecord(
                block_type="document",
                title="全文",
                text=preview,
                start_offset=start,
                end_offset=end,
                confidence=0.3,
                inferred=True,
            )
        )
    return records


def _build_field_candidates(
    parsed_resume: ParsedResume,
    blocks: list[ResumeBlockRecord],
    document: TextDocument,
) -> list[FieldCandidateRecord]:
    rule_candidates = _build_compat_field_candidates(parsed_resume)
    section_candidates = _build_section_field_candidates(parsed_resume, blocks, document)
    missing_candidates = _build_missing_field_candidates(parsed_resume, section_candidates)
    return _dedupe_candidates([*rule_candidates, *section_candidates, *missing_candidates])


def _build_compat_field_candidates(parsed_resume: ParsedResume) -> list[FieldCandidateRecord]:
    data = parsed_resume.candidate_data
    candidates: list[FieldCandidateRecord] = []
    for source in parsed_resume.field_sources:
        field_name = str(source.get("field_name"))
        confidence = _coerce_confidence(source.get("confidence"))
        value = data.get(field_name) if field_name in data else source.get("extracted_value")
        selected = _selected(value, confidence)
        candidates.append(
            FieldCandidateRecord(
                field_name=field_name,
                value_json=value,
                source_text=source.get("source_text"),
                extractor="rules_ai_compat",
                confidence=confidence,
                selected=selected,
                rejection_reason=None if selected else "missing_or_low_confidence",
            )
        )
    return candidates


def _build_section_field_candidates(
    parsed_resume: ParsedResume,
    blocks: list[ResumeBlockRecord],
    document: TextDocument,
) -> list[FieldCandidateRecord]:
    data = parsed_resume.candidate_data
    candidates: list[FieldCandidateRecord] = []
    block_by_type = _first_block_by_type(blocks)
    source_confidence = _source_confidence_by_field(parsed_resume)
    basics_source = _basics_source_text(block_by_type.get("profile"), document)

    for field_name in BASIC_FIELDS:
        value = data.get(field_name)
        confidence = _section_confidence(source_confidence.get(field_name), 0.72, basics_source)
        if _has_value(value):
            candidates.append(
                FieldCandidateRecord(
                    field_name=field_name,
                    value_json=value,
                    source_text=_source_text_for_value(document.source, value, basics_source),
                    extractor="section:basics:rules",
                    confidence=confidence,
                    selected=confidence >= 0.5,
                    rejection_reason=None if confidence >= 0.5 else "low_confidence",
                )
            )

    for field_name, block_type in SECTION_FIELD_SOURCES.items():
        value = data.get(field_name)
        block = block_by_type.get(block_type)
        source_text = _section_value_source(value, block, document.source)
        confidence = _section_confidence(source_confidence.get(field_name), 0.68, source_text)
        if _has_value(value):
            candidates.append(
                FieldCandidateRecord(
                    field_name=field_name,
                    value_json=value,
                    source_text=source_text,
                    extractor=f"section:{_extractor_section_name(block_type)}:rules",
                    confidence=confidence,
                    selected=confidence >= 0.5,
                    rejection_reason=None if confidence >= 0.5 else "low_confidence",
                )
            )
            if field_name in ITEM_LEVEL_FIELDS and isinstance(value, list):
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    item_source = _item_source_text(item, document.source)
                    item_confidence = _section_confidence(source_confidence.get(field_name), 0.66, item_source)
                    candidates.append(
                        FieldCandidateRecord(
                            field_name=field_name,
                            value_json=[item],
                            source_text=item_source,
                            extractor=f"section:{_extractor_section_name(block_type)}:item:rules",
                            confidence=item_confidence,
                            selected=item_confidence >= 0.5,
                            rejection_reason=None if item_confidence >= 0.5 else "low_confidence",
                        )
                    )

    return candidates


def _build_missing_field_candidates(
    parsed_resume: ParsedResume,
    section_candidates: list[FieldCandidateRecord],
) -> list[FieldCandidateRecord]:
    present_fields = {item.field_name for item in section_candidates if _has_value(item.value_json)}
    candidates = []
    for field_name in parsed_resume.candidate_data.get("low_confidence_fields") or []:
        if field_name in present_fields:
            continue
        candidates.append(
            FieldCandidateRecord(
                field_name=field_name,
                value_json=None,
                source_text=None,
                extractor=LOW_CONFIDENCE_EXTRACTOR.get(field_name, "section:unknown:rules"),
                confidence=0.15,
                selected=False,
                rejection_reason="missing_required_field",
            )
        )
    return candidates


def _quality_warnings(parsed_resume: ParsedResume, blocks: list[ResumeBlockRecord]) -> list[str]:
    data = parsed_resume.candidate_data
    warnings = []
    low_confidence = data.get("low_confidence_fields") or []
    if low_confidence:
        warnings.append(f"低置信字段：{', '.join(low_confidence[:8])}")
    if not data.get("project_experiences"):
        warnings.append("未结构化出项目经历")
    if not data.get("work_experiences"):
        warnings.append("未结构化出工作经历")
    if not data.get("education") and not any(block.block_type == "education" for block in blocks):
        warnings.append("未识别到教育经历段落")
    return warnings


def _quality_score(
    parsed_resume: ParsedResume,
    blocks: list[ResumeBlockRecord],
    field_candidates: list[FieldCandidateRecord],
) -> float:
    data = parsed_resume.candidate_data
    score = 100.0
    score -= min(40, sum(LOW_CONFIDENCE_WEIGHTS.get(field, 2) for field in data.get("low_confidence_fields") or []))
    if not data.get("phone") and not data.get("email"):
        score -= 12
    if not data.get("education"):
        score -= 8
    if not data.get("project_experiences"):
        score -= 8
    if not data.get("work_experiences"):
        score -= 5
    if not blocks:
        score -= 10
    selected_count = sum(1 for item in field_candidates if item.selected)
    if selected_count < 5:
        score -= 10
    return max(0.0, min(100.0, round(score, 1)))


def _first_block_by_type(blocks: list[ResumeBlockRecord]) -> dict[str, ResumeBlockRecord]:
    result: dict[str, ResumeBlockRecord] = {}
    for block in blocks:
        result.setdefault(block.block_type, block)
    return result


def _source_confidence_by_field(parsed_resume: ParsedResume) -> dict[str, float]:
    result = {}
    for source in parsed_resume.field_sources:
        field_name = source.get("field_name")
        confidence = _coerce_confidence(source.get("confidence"))
        if isinstance(field_name, str) and confidence is not None:
            result[field_name] = max(result.get(field_name, 0), confidence)
    return result


def _basics_source_text(block: ResumeBlockRecord | None, document: TextDocument) -> str:
    if block and block.text:
        return block.text
    return "\n".join(document.lines[:10])


def _section_value_source(
    value: Any,
    block: ResumeBlockRecord | None,
    full_text: str,
) -> str | None:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            source = _item_source_text(first, full_text)
            if source:
                return source
        if isinstance(first, str) and first.strip():
            return first
    if block and block.text:
        return block.text[:1200]
    return _source_text_for_value(full_text, value, None)


def _item_source_text(item: dict[str, Any], full_text: str, max_chars: int = 260) -> str | None:
    raw = item.get("raw") or item.get("description") or item.get("name")
    if not isinstance(raw, str) or not raw.strip():
        return None
    parts = [part.strip() for part in re.split(r"[；;]\s*", raw) if part.strip()]
    for size in (3, 2, 1):
        candidate = "\n".join(parts[:size])
        if candidate and len(candidate) <= max_chars and candidate in full_text:
            return candidate
    for part in parts:
        if part and part in full_text:
            return part[:max_chars]
    compact = raw.strip()
    return compact[:max_chars] if compact else None


def _source_text_for_value(full_text: str, value: Any, fallback: str | None) -> str | None:
    if not _has_value(value):
        return fallback
    if isinstance(value, list):
        for item in value:
            source = _source_text_for_value(full_text, item, None)
            if source:
                return source
        return fallback
    if isinstance(value, dict):
        for key in ["raw", "name", "company", "school", "title", "description"]:
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip() and raw in full_text:
                return raw
        return fallback
    needle = str(value).strip()
    if needle and needle in full_text:
        return needle
    return fallback


def _section_confidence(rule_confidence: float | None, base: float, source_text: str | None) -> float:
    confidence = rule_confidence if rule_confidence is not None else base
    if not source_text:
        confidence = min(confidence, 0.45)
    return round(max(0.0, min(0.98, confidence)), 2)


def _extractor_section_name(block_type: str) -> str:
    return "projects" if block_type == "project" else block_type


def _selected(value: Any, confidence: float | None) -> bool:
    return _has_value(value) and (confidence is None or confidence >= 0.5)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe_candidates(candidates: list[FieldCandidateRecord]) -> list[FieldCandidateRecord]:
    seen: set[tuple[str, str, str]] = set()
    result = []
    for candidate in candidates:
        key = (
            candidate.field_name,
            candidate.extractor,
            _candidate_value_key(candidate.value_json),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result


def _candidate_value_key(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(_candidate_value_key(item) for item in value[:5])
    if isinstance(value, dict):
        return str(value.get("raw") or value.get("name") or value.get("company") or value)
    return str(value)


def _locate_span(source: str, needle: str | None) -> tuple[int | None, int | None]:
    if not needle:
        return None, None
    start = source.find(needle)
    if start < 0:
        return None, None
    return start, start + len(needle)
