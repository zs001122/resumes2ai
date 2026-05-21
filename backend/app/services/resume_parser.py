import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.ai.base import AIProviderError
from app.services.ai.factory import get_ai_provider


PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*年")
YEAR_RANGE_RE = re.compile(
    r"((?:19|20)\d{2}(?:[./-]\d{1,2}|年\d{1,2}月?)?\s*(?:-|至|~|—|到)\s*(?:至今|现在|今|(?:19|20)\d{2}(?:[./-]\d{1,2}|年\d{1,2}月?)?))"
)
DATE_POINT_RE = re.compile(r"((?:19|20)\d{2})(?:[./-](\d{1,2})|年(\d{1,2})月?)?")

SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node",
    "FastAPI",
    "Django",
    "Flask",
    "Spring",
    "Spring Boot",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Linux",
    "Docker",
    "Kubernetes",
    "SQL",
    "Excel",
    "Pandas",
    "Power BI",
    "Tableau",
    "Git",
    "Nginx",
    "AWS",
    "Azure",
]

EDUCATION_KEYWORDS = ["博士", "硕士", "研究生", "本科", "大专", "专科"]
CITY_KEYWORDS = ["广州", "深圳", "上海", "北京", "杭州", "成都", "武汉", "南京", "佛山", "东莞"]
LANGUAGE_KEYWORDS = ["英语", "日语", "韩语", "粤语", "普通话", "CET-4", "CET-6", "雅思", "托福"]

ORG_ALIASES = {
    "北大": "北京大学",
    "清华": "清华大学",
    "浙大": "浙江大学",
    "复旦": "复旦大学",
    "上交": "上海交通大学",
    "中大": "中山大学",
    "华工": "华南理工大学",
}

AI_RESUME_SCHEMA_HINT = {
    "name": "张三",
    "city": "广州",
    "current_company": "某某科技有限公司",
    "current_title": "后端开发工程师",
    "years_of_experience": 3.5,
    "highest_education": "本科",
    "skills": ["精通 Python", "熟悉 React", "了解 Kubernetes"],
    "education": [{"school": "北京大学", "degree": "本科", "major": "计算机科学", "time_range": "2016.09-2020.06"}],
    "work_experiences": [
        {
            "company": "某某科技有限公司",
            "title": "后端开发工程师",
            "time_range": "2021.03-至今",
            "description": "负责业务系统接口、数据处理和稳定性建设",
        }
    ],
    "project_experiences": [
        {
            "name": "招聘数据平台",
            "role": "后端开发",
            "technologies": ["Python", "FastAPI"],
            "description": "负责简历解析、候选人筛选和报表服务",
        }
    ],
    "certifications": ["PMP"],
    "languages": ["英语 CET-6"],
    "awards": ["校级优秀毕业生"],
    "self_evaluation": "自然语言个人简介摘要",
}

SECTION_ALIASES = {
    "education": ["教育经历", "教育背景", "学历背景", "教育信息"],
    "work": ["工作经历", "工作经验", "实习经历", "任职经历", "职业经历"],
    "project": ["项目经历", "项目经验", "项目实践", "项目介绍"],
    "certifications": ["证书", "资格证书", "专业证书", "技能证书", "认证"],
    "languages": ["语言能力", "外语能力", "语言水平"],
    "awards": ["获奖经历", "获奖情况", "荣誉奖项", "奖项荣誉", "荣誉证书"],
    "self_evaluation": ["自我评价", "个人评价", "个人总结", "自我介绍", "个人优势"],
}

ALL_SECTION_TITLES = [title for titles in SECTION_ALIASES.values() for title in titles]


@dataclass
class ParsedResume:
    candidate_data: dict
    field_sources: list[dict]


def parse_resume_text(file_name: str, text: str) -> ParsedResume:
    source = f"{file_name}\n{text}"
    lines = _normalized_lines(source)
    sections = _extract_sections(lines)

    name = _extract_name_from_filename(file_name) or _extract_name_from_text(lines)
    phone = _first_match(PHONE_RE, source)
    email = _first_match(EMAIL_RE, source)
    city = _first_keyword(CITY_KEYWORDS, source)
    years = _extract_years(source)
    education_level = _first_keyword(EDUCATION_KEYWORDS, source)
    skills = _extract_skills(source)
    education = _extract_education(sections.get("education", []))
    work_experiences = _extract_work_experiences(sections.get("work", []))
    project_experiences = _extract_project_experiences(sections.get("project", []))
    certifications = _extract_list_section(sections.get("certifications", []))
    languages = _extract_languages(sections.get("languages", []), source)
    awards = _extract_list_section(sections.get("awards", []))
    self_evaluation = _extract_paragraph(sections.get("self_evaluation", []))
    current_title = _extract_title_from_filename(file_name) or _first_work_value(work_experiences, "title")
    current_company = _first_work_value(work_experiences, "company")

    candidate_data = {
        "name": name,
        "phone": phone,
        "email": email,
        "city": city,
        "current_company": current_company,
        "current_title": current_title,
        "years_of_experience": years,
        "highest_education": education_level,
        "skills": skills,
        "education": [_normalize_org_item(item, "school") for item in education],
        "work_experiences": [_normalize_org_item(item, "company") for item in work_experiences],
        "project_experiences": project_experiences,
        "certifications": certifications,
        "languages": languages,
        "awards": awards,
        "self_evaluation": self_evaluation,
        "low_confidence_fields": [],
    }
    candidate_data["low_confidence_fields"] = _low_confidence_fields(candidate_data)

    field_sources = [
        _source("name", name, file_name if name and name in file_name else name, 0.8 if name else 0.2, source),
        _source("phone", phone, phone, 0.95 if phone else 0.1, source),
        _source("email", email, email, 0.95 if email else 0.1, source),
        _source("city", city, city, 0.7 if city else 0.1, source),
        _source(
            "years_of_experience",
            str(years) if years is not None else None,
            _first_match(YEARS_RE, source),
            0.65 if years is not None else 0.1,
            source,
        ),
        _source("highest_education", education_level, education_level, 0.7 if education_level else 0.1, source),
        _source("current_company", current_company, current_company, 0.65 if current_company else 0.1, source),
        _source("current_title", current_title, current_title or file_name, 0.65 if current_title else 0.1, source),
        _source("skills", ", ".join(skills) if skills else None, _first_keyword(skills, source), 0.75 if skills else 0.1, source),
        _source("education", _stringify_items(education), _first_raw(education), 0.7 if education else 0.1, source),
        _source("work_experiences", _stringify_items(work_experiences), _first_raw(work_experiences), 0.7 if work_experiences else 0.1, source),
        _source("project_experiences", _stringify_items(project_experiences), _first_raw(project_experiences), 0.7 if project_experiences else 0.1, source),
        _source("certifications", "\n".join(certifications) if certifications else None, certifications[0] if certifications else None, 0.75 if certifications else 0.1, source),
        _source("languages", "\n".join(languages) if languages else None, languages[0] if languages else None, 0.65 if languages else 0.1, source),
        _source("awards", "\n".join(awards) if awards else None, awards[0] if awards else None, 0.65 if awards else 0.1, source),
        _source("self_evaluation", self_evaluation, self_evaluation, 0.65 if self_evaluation else 0.1, source),
    ]
    return ParsedResume(candidate_data=candidate_data, field_sources=field_sources)


async def parse_resume_text_with_ai(file_name: str, text: str) -> ParsedResume:
    rules = parse_resume_text(file_name, text)
    if not settings.ai_resume_parse_enabled:
        return rules
    try:
        ai_payload = await _extract_resume_with_ai(file_name, text, rules.candidate_data)
    except AIProviderError:
        return rules
    except Exception:
        return rules
    return _merge_ai_payload(rules, ai_payload, f"{file_name}\n{text}")


async def _extract_resume_with_ai(file_name: str, text: str, rule_data: dict) -> dict[str, Any]:
    provider = get_ai_provider()
    messages = [
        {
            "role": "system",
            "content": (
                "你是简历结构化抽取助手。规则层已经抽取手机号、邮箱、明确键值对、学校/公司归一化和可计算工作年限。"
                "请主要补全自然语言职责总结、技能熟练度、工作/项目起止时间、无结构项目描述、自我评价和中英文混合文本。"
                "不要编造简历没有的信息；不确定时返回空数组或 null。"
                "技能请保留熟练度措辞，例如：精通 Python、熟悉 React、了解 Kubernetes。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"文件名：{file_name}\n"
                f"规则抽取结果：{rule_data}\n"
                f"简历全文：\n{text[:12000]}"
            ),
        },
    ]
    return await provider.chat_json(messages, AI_RESUME_SCHEMA_HINT)


def _merge_ai_payload(rules: ParsedResume, ai_payload: dict[str, Any], source: str) -> ParsedResume:
    merged = dict(rules.candidate_data)
    protected_fields = {"phone", "email"}
    fill_only_fields = {"name", "city", "years_of_experience", "highest_education", "current_company", "current_title"}

    for field in fill_only_fields:
        if not merged.get(field) and ai_payload.get(field):
            merged[field] = ai_payload[field]

    for field in protected_fields:
        merged[field] = rules.candidate_data.get(field)

    for field in ["skills", "education", "work_experiences", "project_experiences", "certifications", "languages", "awards"]:
        ai_value = ai_payload.get(field)
        if isinstance(ai_value, list) and ai_value:
            merged[field] = _merge_list_values(merged.get(field, []), ai_value, field)

    if not merged.get("self_evaluation") and isinstance(ai_payload.get("self_evaluation"), str):
        merged["self_evaluation"] = ai_payload["self_evaluation"].strip() or None

    merged["education"] = [_normalize_org_item(item, "school") for item in merged.get("education", []) if isinstance(item, dict)]
    merged["work_experiences"] = [
        _normalize_org_item(item, "company") for item in merged.get("work_experiences", []) if isinstance(item, dict)
    ]
    merged["low_confidence_fields"] = _low_confidence_fields(merged)

    ai_sources = []
    for field in ["skills", "work_experiences", "project_experiences", "self_evaluation"]:
        if ai_payload.get(field):
            ai_sources.append(
                _source(field, _field_value_for_source(merged.get(field)), _field_value_for_source(ai_payload.get(field)), 0.55, source)
            )
    return ParsedResume(candidate_data=merged, field_sources=[*rules.field_sources, *ai_sources])


def _normalized_lines(value: str) -> list[str]:
    return [line.strip(" \t\r\n-•●*") for line in value.splitlines() if line.strip()]


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {key: [] for key in SECTION_ALIASES}
    current: str | None = None
    for line in lines:
        section = _section_key(line)
        if section:
            current = section
            remainder = _strip_section_title(line, section)
            if remainder:
                sections[current].append(remainder)
            continue
        if current:
            sections[current].append(line)
    return sections


def _section_key(line: str) -> str | None:
    clean = re.sub(r"[:：\s]+$", "", line.strip())
    for key, titles in SECTION_ALIASES.items():
        if clean in titles or any(clean.startswith(f"{title}：") or clean.startswith(f"{title}:") for title in titles):
            return key
    if len(clean) <= 12:
        for key, titles in SECTION_ALIASES.items():
            if any(clean.startswith(title) for title in titles):
                return key
    return None


def _strip_section_title(line: str, section: str) -> str:
    for title in SECTION_ALIASES[section]:
        pattern = rf"^\s*{re.escape(title)}\s*[:：]\s*"
        stripped = re.sub(pattern, "", line)
        if stripped != line:
            return stripped.strip()
    return ""


def _extract_education(lines: list[str]) -> list[dict]:
    items = []
    for line in _meaningful_lines(lines):
        degree = _first_keyword(EDUCATION_KEYWORDS, line)
        time_range = _first_match(YEAR_RANGE_RE, line)
        normalized = line.replace(time_range, "").strip() if time_range else line
        parts = _split_compact_line(normalized)
        school = _first_part_matching(parts, ["大学", "学院", "学校"])
        major = _extract_major(parts, school, degree)
        items.append(
            {
                "school": school,
                "degree": degree,
                "major": major,
                "time_range": time_range,
                "raw": line,
            }
        )
    return items[:5]


def _extract_work_experiences(lines: list[str]) -> list[dict]:
    items = []
    for line in _meaningful_lines(lines):
        time_range = _first_match(YEAR_RANGE_RE, line)
        without_time = line.replace(time_range, "").strip(" -|｜，,") if time_range else line
        parts = _split_compact_line(without_time)
        company = _extract_company(without_time, parts)
        title = _guess_title(parts, company)
        if not any([company, title, time_range]):
            continue
        items.append(
            {
                "company": company,
                "title": title,
                "time_range": time_range,
                "description": _strip_known_parts(without_time, [company, title]),
                "raw": line,
            }
        )
    return items[:8]


def _extract_project_experiences(lines: list[str]) -> list[dict]:
    items = []
    chunks = _split_section_items(lines)
    for chunk in chunks:
        text = "；".join(chunk)
        first_line = chunk[0]
        name = re.sub(r"^(项目名称|项目)[:：]\s*", "", first_line).strip()
        role = _extract_labeled_value(text, ["项目角色", "角色", "职责"])
        technologies = [skill for skill in _extract_skills(text) if skill]
        items.append(
            {
                "name": name[:80] if name else "项目经历",
                "role": role,
                "technologies": technologies,
                "description": text,
                "raw": text,
            }
        )
    return items[:8]


def _extract_list_section(lines: list[str]) -> list[str]:
    results = []
    for line in _meaningful_lines(lines):
        for item in re.split(r"[；;]", line):
            item = item.strip(" ，,。")
            if item and item not in results:
                results.append(item)
    return results[:12]


def _extract_languages(lines: list[str], source: str) -> list[str]:
    results = _extract_list_section(lines)
    for keyword in LANGUAGE_KEYWORDS:
        if keyword in source and keyword not in results:
            results.append(keyword)
    return results[:12]


def _extract_paragraph(lines: list[str]) -> str | None:
    values = _meaningful_lines(lines)
    if not values:
        return None
    return "\n".join(values[:6])


def _meaningful_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line and not _section_key(line) and line not in ALL_SECTION_TITLES]


def _split_section_items(lines: list[str]) -> list[list[str]]:
    items: list[list[str]] = []
    current: list[str] = []
    for line in _meaningful_lines(lines):
        starts_new = bool(YEAR_RANGE_RE.search(line)) or re.match(r"^(项目名称|项目)[:：]", line)
        if current and starts_new:
            items.append(current)
            current = []
        current.append(line)
    if current:
        items.append(current)
    return items


def _extract_name_from_filename(file_name: str) -> str | None:
    stem = Path(file_name).stem
    match = re.search(r"】[-_ ]?([^-_ ]{2,8})[-_ ]", stem)
    if match:
        return match.group(1)
    if "-" in stem:
        candidate = stem.split("-")[-1].strip()
        if 2 <= len(candidate) <= 8 and not any(char.isdigit() for char in candidate):
            return candidate
    return None


def _extract_name_from_text(lines: list[str]) -> str | None:
    for line in lines[:8]:
        match = re.search(r"(?:姓名|候选人)[:：]\s*([\u4e00-\u9fa5A-Za-z·]{2,20})", line)
        if match:
            return match.group(1)
    return None


def _extract_title_from_filename(file_name: str) -> str | None:
    stem = Path(file_name).stem
    if "】" in stem:
        title = stem.split("】", 1)[0].lstrip("【").strip()
        return title or None
    if "-" in stem:
        return stem.split("-", 1)[0].strip() or None
    return None


def _first_work_value(items: list[dict], key: str) -> str | None:
    for item in items:
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _first_match(pattern: re.Pattern[str], value: str) -> str | None:
    match = pattern.search(value)
    return match.group(1) if match and match.groups() else (match.group(0) if match else None)


def _first_keyword(keywords: list[str], value: str) -> str | None:
    for keyword in keywords:
        if keyword in value:
            return keyword
    return None


def _extract_years(value: str) -> float | None:
    matches = [float(match.group(1)) for match in YEARS_RE.finditer(value)]
    range_years = _years_from_date_ranges(value)
    if range_years is not None:
        matches.append(range_years)
    if not matches:
        return 0 if any(keyword in value for keyword in ["应届", "实习生"]) else None
    return max(matches)


def _years_from_date_ranges(value: str) -> float | None:
    starts = []
    ends = []
    today = date.today()
    for raw_range in YEAR_RANGE_RE.findall(value):
        points = DATE_POINT_RE.findall(raw_range)
        if not points:
            continue
        start_year, start_month_1, start_month_2 = points[0]
        starts.append(date(int(start_year), int(start_month_1 or start_month_2 or 1), 1))
        if re.search(r"至今|现在|今", raw_range):
            ends.append(today)
        elif len(points) > 1:
            end_year, end_month_1, end_month_2 = points[-1]
            ends.append(date(int(end_year), int(end_month_1 or end_month_2 or 12), 1))
    if not starts or not ends:
        return None
    months = (max(ends).year - min(starts).year) * 12 + (max(ends).month - min(starts).month)
    return round(max(0, months) / 12, 1)


def _extract_skills(value: str) -> list[str]:
    lower = value.lower()
    result: list[str] = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in lower and skill not in result:
            result.append(skill)
    return result


def _split_compact_line(line: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s+|[|｜,/，、]", line) if part.strip()]


def _first_part_matching(parts: list[str], keywords: list[str]) -> str | None:
    for part in parts:
        if any(keyword in part for keyword in keywords):
            return part
    return None


def _extract_company(value: str, parts: list[str]) -> str | None:
    match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9（）()]{2,40}(?:有限公司|公司|集团|科技|网络|信息))", value)
    if match:
        return match.group(1)
    return _first_part_matching(parts, ["有限公司", "公司", "集团", "科技", "网络", "信息"])


def _extract_major(parts: list[str], school: str | None, degree: str | None) -> str | None:
    for part in parts:
        if part not in {school, degree} and not YEAR_RANGE_RE.search(part):
            if any(word in part for word in ["专业", "工程", "科学", "管理", "会计", "金融", "设计", "语言"]):
                return part
    return None


def _guess_title(parts: list[str], company: str | None) -> str | None:
    title_keywords = ["工程师", "开发", "经理", "主管", "专员", "分析师", "产品", "运营", "设计", "实习"]
    for part in parts:
        if part != company and any(keyword in part for keyword in title_keywords):
            return part
    return None


def _strip_known_parts(value: str, parts: list[str | None]) -> str | None:
    result = value
    for part in parts:
        if part:
            result = result.replace(part, "")
    result = re.sub(r"\s{2,}", " ", result).strip(" -|｜，,")
    return result or None


def _extract_labeled_value(value: str, labels: list[str]) -> str | None:
    for label in labels:
        match = re.search(rf"{label}[:：]\s*([^；;。]+)", value)
        if match:
            return match.group(1).strip()
    return None


def _normalize_org_item(item: dict, key: str) -> dict:
    value = item.get(key)
    if isinstance(value, str):
        item = dict(item)
        item[key] = _normalize_org_name(value)
    return item


def _normalize_org_name(value: str) -> str:
    clean = value.strip()
    return ORG_ALIASES.get(clean, clean)


def _low_confidence_fields(candidate_data: dict) -> list[str]:
    fields = {
        "name": candidate_data.get("name"),
        "phone": candidate_data.get("phone"),
        "email": candidate_data.get("email"),
        "city": candidate_data.get("city"),
        "years_of_experience": candidate_data.get("years_of_experience"),
        "highest_education": candidate_data.get("highest_education"),
        "current_title": candidate_data.get("current_title"),
        "education": candidate_data.get("education"),
        "work_experiences": candidate_data.get("work_experiences"),
        "project_experiences": candidate_data.get("project_experiences"),
        "certifications": candidate_data.get("certifications"),
    }
    return [field_name for field_name, value in fields.items() if value in (None, "", [])]


def _merge_list_values(rule_values: list, ai_values: list, field: str) -> list:
    values = [*rule_values]
    seen = {_dedupe_key(value) for value in values}
    for value in ai_values:
        normalized = _normalize_ai_list_item(value, field)
        key = _dedupe_key(normalized)
        if normalized not in (None, "", []) and key not in seen:
            values.append(normalized)
            seen.add(key)
    return values[:12]


def _normalize_ai_list_item(value: Any, field: str):
    if field in {"education", "work_experiences", "project_experiences"}:
        return value if isinstance(value, dict) else {"raw": str(value)}
    return str(value).strip() if value is not None else None


def _dedupe_key(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("raw") or value.get("name") or value.get("company") or value.get("school") or value)
    return str(value)


def _field_value_for_source(value: Any) -> str | None:
    if value in (None, "", []):
        return None
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return "\n".join(value)
        return "\n".join(str(item.get("raw") or item) if isinstance(item, dict) else str(item) for item in value)
    return str(value)


def _stringify_items(items: list[dict]) -> str | None:
    if not items:
        return None
    return "\n".join(str(item.get("raw") or item) for item in items)


def _first_raw(items: list[dict]) -> str | None:
    if not items:
        return None
    value = items[0].get("raw")
    return str(value) if value else None


def _source(field_name: str, value: str | None, source_text: str | None, confidence: float, full_text: str) -> dict:
    start, end = _locate_span(full_text, source_text or value)
    return {
        "field_name": field_name,
        "extracted_value": value,
        "confidence": confidence,
        "source_text": source_text,
        "page_number": None,
        "text_start_offset": start,
        "text_end_offset": end,
        "bounding_box": None,
    }


def _locate_span(full_text: str, needle: str | None) -> tuple[int | None, int | None]:
    if not needle:
        return None, None
    index = full_text.find(needle)
    if index < 0:
        return None, None
    return index, index + len(needle)
