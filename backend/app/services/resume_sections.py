from __future__ import annotations

import re
from dataclasses import dataclass


SECTION_ALIASES = {
    "education": ["教育经历", "教育背景", "学历背景", "教育信息"],
    "work": ["工作经历", "工作经验", "实习经历", "任职经历", "职业经历"],
    "project": ["项目经历", "项目经验", "项目实践", "项目介绍", "校园个人项目"],
    "skills": ["专业技能", "技能清单", "技能特长"],
    "intention": ["求职意向"],
    "profile": ["基本信息", "个人信息"],
    "certifications": ["证书", "资格证书", "专业证书", "技能证书", "认证", "荣誉证书"],
    "languages": ["语言能力", "外语能力", "语言水平"],
    "awards": ["获奖经历", "获奖情况", "荣誉奖项", "奖项荣誉"],
    "campus": ["校园经历", "校园活动", "校园实践", "校内实践", "校内外实践活动"],
    "self_evaluation": ["自我评价", "个人评价", "个人总结", "自我介绍", "个人优势"],
}

ALL_SECTION_TITLES = [title for titles in SECTION_ALIASES.values() for title in titles]


@dataclass(frozen=True)
class ResumeSection:
    key: str
    title: str | None
    lines: list[str]
    confidence: float = 0.8
    inferred: bool = False


def normalized_lines(value: str) -> list[str]:
    return [_normalize_line(line) for line in value.splitlines() if line.strip()]


def extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {key: [] for key in SECTION_ALIASES}
    current: str | None = None
    for line in lines:
        section = section_key(line)
        if section:
            current = section
            remainder = strip_section_title(line, section)
            if remainder:
                sections[current].append(remainder)
            continue
        embedded = split_embedded_section(line)
        if embedded:
            before, embedded_section, remainder = embedded
            if current and before:
                sections[current].append(before)
            current = embedded_section
            if remainder:
                sections[current].append(remainder)
            continue
        if current:
            sections[current].append(line)
    return augment_inferred_sections(sections, lines)


def section_blocks(lines: list[str]) -> list[ResumeSection]:
    sections = extract_sections(lines)
    blocks = []
    for key, section_lines in sections.items():
        if section_lines:
            blocks.append(ResumeSection(key=key, title=_primary_title(key), lines=section_lines))
    return blocks


def section_key(line: str) -> str | None:
    clean = re.sub(r"[:：\s]+$", "", line.strip())
    compact_clean = re.sub(r"\s+", "", clean)
    for key, titles in SECTION_ALIASES.items():
        compact_titles = [re.sub(r"\s+", "", title) for title in titles]
        if compact_clean in compact_titles or any(
            compact_clean.startswith(f"{title}：") or compact_clean.startswith(f"{title}:") for title in compact_titles
        ):
            return key
    if len(clean) <= 12:
        for key, titles in SECTION_ALIASES.items():
            if any(compact_clean.startswith(re.sub(r"\s+", "", title)) for title in titles):
                return key
    return None


def strip_section_title(line: str, section: str) -> str:
    for title in SECTION_ALIASES[section]:
        patterns = [
            rf"^\s*{re.escape(title)}\s*[:：]\s*",
            rf"^\s*{_spaced_title_pattern(title)}\s*[:：]?\s*",
        ]
        for pattern in patterns:
            stripped = re.sub(pattern, "", line)
            if stripped != line:
                return stripped.strip()
    return ""


def split_embedded_section(line: str) -> tuple[str, str, str] | None:
    for key, titles in SECTION_ALIASES.items():
        for title in titles:
            pattern = rf"(.+[。；;])\s*(?:{re.escape(title)}|{_spaced_title_pattern(title)})\s*[:：]?\s*(.*)$"
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip(), key, match.group(2).strip()
    return None


def meaningful_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line and not section_key(line) and line not in ALL_SECTION_TITLES]


def split_section_items(lines: list[str]) -> list[list[str]]:
    items: list[list[str]] = []
    current: list[str] = []
    for line in meaningful_lines(lines):
        starts_new = bool(_date_range_search(line) and not _is_date_only_line(line)) or re.match(r"^(项目名称|项目)[:：]", line)
        if current and starts_new:
            items.append(current)
            current = []
        current.append(line)
    if current:
        items.append(current)
    return items


def augment_inferred_sections(sections: dict[str, list[str]], lines: list[str]) -> dict[str, list[str]]:
    if sections.get("work") and sections.get("project"):
        return sections
    inferred_work, inferred_project = _infer_work_project_sections(lines)
    if not sections.get("work") and inferred_work:
        sections["work"] = inferred_work
    if not sections.get("project") and inferred_project:
        sections["project"] = inferred_project
    return sections


def _infer_work_project_sections(lines: list[str]) -> tuple[list[str], list[str]]:
    work: list[str] = []
    project: list[str] = []
    current: str | None = None
    for line in lines:
        if section_key(line) in {
            "education",
            "skills",
            "intention",
            "profile",
            "certifications",
            "languages",
            "awards",
            "campus",
            "self_evaluation",
        }:
            current = None
            continue
        if _looks_like_project_header(line):
            current = "project"
            project.append(line)
            continue
        if current == "project" and _is_project_detail_line(line):
            project.append(line)
            continue
        if _looks_like_work_header(line):
            current = "work"
            work.append(line)
            continue
        if current == "project" and line:
            project.append(line)
        elif current == "work" and line:
            work.append(line)
    return work, project


def _looks_like_work_header(line: str) -> bool:
    if _is_project_detail_line(line) or _is_campus_context(line):
        return False
    return bool(
        re.search(r"(有限公司|公司|集团).{0,20}(工程师|开发|分析师|实习|ETL|etl)", line)
        or re.search(r"(工程师|开发|分析师|实习|ETL|etl).{0,8}(19|20)\d{2}", line)
    )


def _looks_like_project_header(line: str) -> bool:
    if line in ALL_SECTION_TITLES:
        return False
    has_project_name_shape = "项目" in line and len(line) <= 60 and not any(mark in line for mark in "，,。；;")
    return bool(
        (has_project_name_shape and not line.startswith(("项目概况", "项目简介", "项目职责", "项目主要点", "项目技术", "项目描述")))
        or re.search(r".{2,40}(系统|平台|网站|小车|服务站).{0,12}(工程师|开发|ETL|etl|项目).*(19|20)\d{2}", line)
    )


def _is_project_detail_line(line: str) -> bool:
    return line.startswith(("工作岗位", "负责工作", "项目职责", "项目概况", "项目简介", "技术描述", "技术架构", "项目技术"))


def _is_campus_context(line: str) -> bool:
    campus_terms = ("大学", "学院", "学校", "实验室", "教学楼", "电子信息楼", "课程", "毕设", "毕业设计", "竞赛", "实训")
    company_terms = ("有限公司", "公司", "集团")
    return any(term in line for term in campus_terms) and not any(term in line for term in company_terms)


def _normalize_line(line: str) -> str:
    stripped = line.strip(" \t\r\n-•●*")
    stripped = re.sub(r"\s{2,}", " ", stripped)
    return _normalize_spaced_section_title(stripped)


def _normalize_spaced_section_title(line: str) -> str:
    for titles in SECTION_ALIASES.values():
        for title in titles:
            line = re.sub(rf"(?<!\S){_spaced_title_pattern(title)}(?!\S)", title, line)
    return line


def _spaced_title_pattern(title: str) -> str:
    return r"\s*".join(re.escape(char) for char in title)


def _primary_title(key: str) -> str | None:
    titles = SECTION_ALIASES.get(key) or []
    return titles[0] if titles else None


def _date_range_search(line: str):
    return re.search(
        r"(?:19|20)\d{2}(?:[./-]\d{1,2}|年\s*\d{1,2}\s*月?)?\s*(?:-|至|~|—|到)\s*"
        r"(?:至今|现在|今|(?:19|20)\d{2}(?:[./-]\d{1,2}|年\s*\d{1,2}\s*月?)?)",
        line,
    )


def _is_date_only_line(line: str) -> bool:
    clean = re.sub(r"\s+", "", line.strip(" ：:;；"))
    return bool(
        re.fullmatch(
            r"(?:19|20)\d{2}(?:[./-]\d{1,2}|年\d{1,2}月?)?(?:-|至|~|—|到)(?:至今|现在|今|(?:19|20)\d{2}(?:[./-]\d{1,2}|年\d{1,2}月?)?)",
            clean,
        )
    )
