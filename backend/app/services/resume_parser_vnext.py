from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.services.resume_parser import ParsedResume, parse_resume_text_with_ai
from app.services.resume_sections import normalized_lines, section_blocks

PARSER_VERSION = "resume-parser-vnext-0.1"


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
    field_candidates = _build_field_candidates(parsed_resume)
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


def _build_field_candidates(parsed_resume: ParsedResume) -> list[FieldCandidateRecord]:
    data = parsed_resume.candidate_data
    candidates: list[FieldCandidateRecord] = []
    for source in parsed_resume.field_sources:
        field_name = str(source.get("field_name"))
        confidence = source.get("confidence")
        value = data.get(field_name) if field_name in data else source.get("extracted_value")
        selected = _has_value(value) and (confidence is None or float(confidence) >= 0.5)
        rejection_reason = None if selected else "missing_or_low_confidence"
        candidates.append(
            FieldCandidateRecord(
                field_name=field_name,
                value_json=value,
                source_text=source.get("source_text"),
                extractor="rules_ai_compat",
                confidence=confidence,
                selected=selected,
                rejection_reason=rejection_reason,
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
    if not any(block.block_type == "education" for block in blocks):
        warnings.append("未识别到教育经历段落")
    return warnings


def _quality_score(
    parsed_resume: ParsedResume,
    blocks: list[ResumeBlockRecord],
    field_candidates: list[FieldCandidateRecord],
) -> float:
    data = parsed_resume.candidate_data
    score = 100.0
    score -= min(40, len(data.get("low_confidence_fields") or []) * 8)
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


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _locate_span(source: str, needle: str | None) -> tuple[int | None, int | None]:
    if not needle:
        return None, None
    start = source.find(needle)
    if start < 0:
        return None, None
    return start, start + len(needle)
