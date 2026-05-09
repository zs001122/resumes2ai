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
    must_have_text = " ".join(job.must_have or [])
    skills = candidate.skills or []
    matched_skills = [skill for skill in skills if skill.lower() in must_have_text.lower()]
    score = 45 + min(35, len(matched_skills) * 10)
    if candidate.years_of_experience is not None:
        score += min(10, candidate.years_of_experience * 2)
    if candidate.highest_education:
        score += 5
    score = max(0, min(100, score))

    weak_points = []
    if not matched_skills:
        weak_points.append("简历技能与岗位必备条件的直接命中较少。")
    if candidate.years_of_experience is None:
        weak_points.append("工作年限需要人工确认。")

    return CandidateMatchCreate(
        score=score,
        level=_level_from_score(score),
        summary=f"已使用本地规则生成临时匹配结果；AI 调用未使用或失败，原因：{reason}",
        matched_points=[f"命中技能：{skill}" for skill in matched_skills] or ["候选人基础信息已完成解析。"],
        weak_points=weak_points,
        risks=["该结果为本地规则兜底评分，建议 HR 复核。"],
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
        "low_confidence_fields": candidate.low_confidence_fields,
    }
