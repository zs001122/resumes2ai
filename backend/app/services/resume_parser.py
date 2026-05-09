import re
from dataclasses import dataclass
from pathlib import Path


PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*年")

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
]

EDUCATION_KEYWORDS = ["博士", "硕士", "研究生", "本科", "大专", "专科"]
CITY_KEYWORDS = ["广州", "深圳", "上海", "北京", "杭州", "成都", "武汉", "南京", "佛山", "东莞"]


@dataclass
class ParsedResume:
    candidate_data: dict
    field_sources: list[dict]


def parse_resume_text(file_name: str, text: str) -> ParsedResume:
    source = f"{file_name}\n{text}"
    name = _extract_name_from_filename(file_name)
    phone = _first_match(PHONE_RE, source)
    email = _first_match(EMAIL_RE, source)
    city = _first_keyword(CITY_KEYWORDS, source)
    years = _extract_years(source)
    education = _first_keyword(EDUCATION_KEYWORDS, source)
    skills = _extract_skills(source)
    current_title = _extract_title_from_filename(file_name)

    low_confidence_fields = []
    for field_name, value in {
        "name": name,
        "phone": phone,
        "email": email,
        "city": city,
        "years_of_experience": years,
        "highest_education": education,
        "current_title": current_title,
    }.items():
        if value in (None, "", []):
            low_confidence_fields.append(field_name)

    candidate_data = {
        "name": name,
        "phone": phone,
        "email": email,
        "city": city,
        "current_company": None,
        "current_title": current_title,
        "years_of_experience": years,
        "highest_education": education,
        "skills": skills,
        "education": [],
        "work_experiences": [],
        "project_experiences": [],
        "low_confidence_fields": low_confidence_fields,
    }

    field_sources = [
        _source("name", name, file_name, 0.8 if name else 0.2),
        _source("phone", phone, phone, 0.95 if phone else 0.1),
        _source("email", email, email, 0.95 if email else 0.1),
        _source("city", city, city, 0.7 if city else 0.1),
        _source("years_of_experience", str(years) if years is not None else None, file_name, 0.65 if years else 0.1),
        _source("highest_education", education, education, 0.7 if education else 0.1),
        _source("current_title", current_title, file_name, 0.6 if current_title else 0.1),
        _source("skills", ", ".join(skills) if skills else None, None, 0.75 if skills else 0.1),
    ]
    return ParsedResume(candidate_data=candidate_data, field_sources=field_sources)


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


def _extract_title_from_filename(file_name: str) -> str | None:
    stem = Path(file_name).stem
    if "】" in stem:
        title = stem.split("】", 1)[0].lstrip("【").strip()
        return title or None
    if "-" in stem:
        return stem.split("-", 1)[0].strip() or None
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
    if not matches:
        return 0 if any(keyword in value for keyword in ["应届", "实习生"]) else None
    return max(matches)


def _extract_skills(value: str) -> list[str]:
    lower = value.lower()
    result: list[str] = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in lower and skill not in result:
            result.append(skill)
    return result


def _source(field_name: str, value: str | None, source_text: str | None, confidence: float) -> dict:
    return {
        "field_name": field_name,
        "extracted_value": value,
        "confidence": confidence,
        "source_text": source_text,
        "page_number": None,
        "text_start_offset": None,
        "text_end_offset": None,
        "bounding_box": None,
    }
