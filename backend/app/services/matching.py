from typing import Any

from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.match import CandidateMatchCreate
from app.services.ai.factory import get_ai_provider


MATCH_SCHEMA_HINT = {
    "score": 86,
    "level": "强推荐",
    "summary": "一句话说明候选人与岗位的匹配情况",
    "matched_points": ["匹配点"],
    "weak_points": ["短板"],
    "risks": ["待确认风险"],
    "interview_questions": ["面试追问"],
}


async def generate_candidate_match(job: Job, candidate: Candidate) -> CandidateMatchCreate:
    try:
        result = await _generate_with_ai(job, candidate)
        return _normalize_ai_result(result)
    except Exception as exc:
        return _fallback_match(job, candidate, str(exc))


async def _generate_with_ai(job: Job, candidate: Candidate) -> dict[str, Any]:
    provider = get_ai_provider()
    messages = [
        {
            "role": "system",
            "content": (
                "你是招聘初筛助手。请只基于岗位相关能力分析候选人与岗位的匹配度。"
                "不要使用性别、婚育、民族等敏感信息作为判断依据。"
                "不确定的内容请标为待确认。"
            ),
        },
        {
            "role": "user",
            "content": f"岗位信息：{_job_payload(job)}\n候选人信息：{_candidate_payload(candidate)}",
        },
    ]
    return await provider.chat_json(messages, MATCH_SCHEMA_HINT)


def _normalize_ai_result(result: dict[str, Any]) -> CandidateMatchCreate:
    score = float(result.get("score", 0))
    score = max(0, min(100, score))
    return CandidateMatchCreate(
        score=score,
        level=str(result.get("level") or _level_from_score(score)),
        summary=str(result.get("summary") or "AI 已生成匹配结果。"),
        matched_points=_as_str_list(result.get("matched_points")),
        weak_points=_as_str_list(result.get("weak_points")),
        risks=_as_str_list(result.get("risks")),
        interview_questions=_as_str_list(result.get("interview_questions")),
    )


def _fallback_match(job: Job, candidate: Candidate, reason: str) -> CandidateMatchCreate:
    direct_score, matched_skills, missing_required = _score_required_skills(job, candidate)
    related_score, related_skills = _score_related_skills(job, candidate)
    project_score, project_points = _score_project_evidence(job, candidate, matched_skills + related_skills)
    experience_score, experience_note = _score_experience(job, candidate)
    education_score, education_note = _score_education(job, candidate)
    location_score, location_note = _score_location(job, candidate)
    risk_penalty, risks = _score_deal_breakers(job, candidate)
    missing_penalty = min(24, len(missing_required) * 8)

    score = direct_score + related_score + project_score + experience_score + education_score + location_score - risk_penalty - missing_penalty
    score = max(0, min(100, score))

    matched_points = []
    if matched_skills:
        matched_points.append(f"必备技能直接命中：{', '.join(matched_skills)}")
    if related_skills:
        matched_points.append(f"岗位相关技能证据：{', '.join(related_skills[:8])}")
    matched_points.extend(project_points)
    for note in [experience_note, education_note, location_note]:
        if note:
            matched_points.append(note)

    weak_points = []
    if missing_required:
        weak_points.append(f"岗位必备技能未明确体现：{', '.join(missing_required)}")
    if not (candidate.project_experiences or []):
        weak_points.append("简历未结构化出明确项目经历，项目证据需要人工复核。")
    if candidate.years_of_experience is None:
        weak_points.append("工作年限需要人工确认。")

    return CandidateMatchCreate(
        score=score,
        level=_level_from_score(score),
        summary=f"已使用本地规则生成临时匹配结果；AI 调用未使用或失败，原因：{reason}",
        matched_points=matched_points or ["候选人基础信息已完成解析。"],
        weak_points=weak_points,
        risks=[*risks, "该结果为本地规则兜底评分，建议 HR 复核。"],
        interview_questions=[
            "请候选人说明与岗位核心要求最相关的项目经历。",
            "请确认简历中未明确的信息是否符合岗位要求。",
        ],
    )


def _level_from_score(score: float) -> str:
    if score >= 85:
        return "强推荐"
    if score >= 70:
        return "可沟通"
    if score >= 55:
        return "备选"
    if score >= 40:
        return "谨慎"
    return "不推荐"


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _score_required_skills(job: Job, candidate: Candidate) -> tuple[float, list[str], list[str]]:
    required = [str(item).strip() for item in (job.must_have or []) if str(item).strip()]
    skills = _candidate_skill_set(candidate)
    matched = [item for item in required if _skill_contains(skills, item)]
    missing = [item for item in required if item not in matched]
    return min(30, len(matched) * 10), matched, missing


def _score_related_skills(job: Job, candidate: Candidate) -> tuple[float, list[str]]:
    skills = _candidate_skill_set(candidate)
    related = [skill for skill in _job_related_skills(job) if skill.lower() in skills]
    return min(12, len(related) * 2), related


def _score_project_evidence(job: Job, candidate: Candidate, evidence_skills: list[str]) -> tuple[float, list[str]]:
    projects = candidate.project_experiences or []
    if not projects:
        return 0, []
    project_text = " ".join(str(project) for project in projects).lower()
    evidence = [skill for skill in evidence_skills if skill.lower() in project_text]
    if not evidence:
        evidence = [skill for skill in _job_related_skills(job) if skill.lower() in project_text]
    if evidence:
        return min(15, 8 + len(set(evidence))), [f"项目经历出现相关技术或职责：{', '.join(sorted(set(evidence))[:8])}"]
    return 5, ["简历包含项目经历，可作为面试追问依据。"]


def _score_experience(job: Job, candidate: Candidate) -> tuple[float, str | None]:
    years = candidate.years_of_experience
    requirement = str(job.experience_required or "")
    if years is None:
        return 3, None
    if any(word in requirement for word in ["应届", "实习", "1 年以内", "1年以内"]):
        if years <= 1:
            return 10, "工作年限符合应届/实习岗位要求。"
        if years <= 3:
            return 6, "工作年限略高于应届/实习要求，需确认求职预期。"
        return 2, None
    return min(10, 4 + years), f"候选人解析工作年限为 {years:g} 年。"


def _score_education(job: Job, candidate: Candidate) -> tuple[float, str | None]:
    required = str(job.education_required or "")
    education = str(candidate.highest_education or "")
    if not education:
        return 2, None
    ranks = {"博士": 5, "硕士": 4, "研究生": 4, "本科": 3, "大专": 2, "专科": 2}
    if "本科" in required and education in {"本科", "硕士", "研究生", "博士"}:
        return 10, f"最高学历满足要求：{education}。"
    if any(word in required for word in ["专科", "大专"]) and ranks.get(education, 0) >= 2:
        return 10, f"最高学历满足要求：{education}。"
    return 6, f"最高学历解析为：{education}。"


def _score_location(job: Job, candidate: Candidate) -> tuple[float, str | None]:
    if job.location and candidate.city and str(job.location) in str(candidate.city):
        return 5, f"城市匹配：{candidate.city}。"
    return 0, None


def _score_deal_breakers(job: Job, candidate: Candidate) -> tuple[float, list[str]]:
    risks = []
    penalty = 0
    deal_breakers = " ".join(job.deal_breakers or [])
    if "没有项目经验" in deal_breakers and not (candidate.project_experiences or []):
        penalty += 10
        risks.append("岗位排除项提到项目经验，但简历未结构化出项目经历。")
    if candidate.low_confidence_fields:
        risks.append(f"低置信字段：{', '.join(candidate.low_confidence_fields[:5])}")
    return penalty, risks


def _candidate_skill_set(candidate: Candidate) -> set[str]:
    values = [str(skill).lower() for skill in (candidate.skills or [])]
    for project in candidate.project_experiences or []:
        if isinstance(project, dict):
            values.extend(str(skill).lower() for skill in project.get("technologies") or [])
            values.append(str(project.get("description") or "").lower())
    return set(values)


def _skill_contains(skills: set[str], required: str) -> bool:
    required_lower = required.lower()
    return any(required_lower in skill or skill in required_lower for skill in skills)


def _job_related_skills(job: Job) -> list[str]:
    text = " ".join(
        [
            str(job.title or ""),
            str(job.department or ""),
            " ".join(job.responsibilities or []),
            " ".join(job.must_have or []),
            " ".join(job.nice_to_have or []),
        ]
    ).lower()
    skills: list[str] = []
    if any(word in text for word in ["软件", "开发", "后端", "接口", "业务系统"]):
        skills.extend(["Java", "Spring", "Spring Boot", "MySQL", "Redis", "SQL", "Linux", "Docker", "Nginx", "Python"])
    if any(word in text for word in ["前端", "react", "vue", "页面"]):
        skills.extend(["JavaScript", "TypeScript", "React", "Vue", "Element Plus"])
    if any(word in text for word in ["数据", "etl", "仓库", "sql"]):
        skills.extend(["Python", "SQL", "MySQL", "ETL", "数据仓库", "Excel"])
    return list(dict.fromkeys(skills))


def _job_payload(job: Job) -> dict[str, Any]:
    return {
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "experience_required": job.experience_required,
        "education_required": job.education_required,
        "responsibilities": job.responsibilities,
        "must_have": job.must_have,
        "nice_to_have": job.nice_to_have,
        "deal_breakers": job.deal_breakers,
        "scoring_dimensions": job.scoring_dimensions,
    }


def _candidate_payload(candidate: Candidate) -> dict[str, Any]:
    return {
        "name": candidate.name,
        "city": candidate.city,
        "current_company": candidate.current_company,
        "current_title": candidate.current_title,
        "years_of_experience": candidate.years_of_experience,
        "highest_education": candidate.highest_education,
        "skills": candidate.skills,
        "education": candidate.education,
        "work_experiences": candidate.work_experiences,
        "project_experiences": candidate.project_experiences,
        "certifications": candidate.certifications,
        "languages": candidate.languages,
        "awards": candidate.awards,
        "self_evaluation": candidate.self_evaluation,
        "low_confidence_fields": candidate.low_confidence_fields,
    }
