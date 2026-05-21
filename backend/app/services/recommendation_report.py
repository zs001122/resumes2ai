from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import CandidateMatch
from app.models.v2 import CandidateMatchExplanation


def build_recommendation_markdown(
    job: Job,
    candidate: Candidate,
    match: CandidateMatch,
    explanations: list[CandidateMatchExplanation],
) -> str:
    lines = [
        f"# 候选人推荐摘要：{candidate.name or '姓名待确认'}",
        "",
        "## 基本信息",
        "",
        f"- 推荐岗位：{job.title}",
        f"- 当前岗位：{candidate.current_title or '待确认'}",
        f"- 当前公司：{candidate.current_company or '待确认'}",
        f"- 当前城市：{candidate.city or '待确认'}",
        f"- 工作年限：{_format_years(candidate.years_of_experience)}",
        f"- 最高学历：{candidate.highest_education or '待确认'}",
        "",
        "## 匹配结论",
        "",
        f"- 匹配分：{match.score:g}",
        f"- 推荐等级：{match.level}",
        f"- 摘要：{match.summary}",
        "",
        "## 推荐理由",
        "",
        *_bullet_lines(match.matched_points, "暂无明确推荐理由，建议结合原简历复核。"),
        "",
        "## 主要亮点",
        "",
        *_bullet_lines(_highlight_items(candidate, match, explanations), "暂无明确亮点，建议补充人工判断。"),
        "",
        "## 项目与证书",
        "",
        *_bullet_lines(_project_and_certificate_items(candidate), "暂无项目或证书信息。"),
        "",
        "## 主要短板",
        "",
        *_bullet_lines(match.weak_points, "暂无明确短板。"),
        "",
        "## 风险与待确认",
        "",
        *_bullet_lines(match.risks, "暂无明确风险点。"),
        "",
        "## 建议面试问题",
        "",
        *_numbered_lines(match.interview_questions, "暂无建议问题。"),
        "",
        "## HR 备注",
        "",
        "- ",
        "",
        "> 本摘要由系统基于岗位标准、候选人简历解析和最新匹配结果生成，仅作沟通辅助材料；最终判断以 HR 和用人部门复核为准。",
        "",
    ]
    return "\n".join(lines)


def _format_years(value: float | None) -> str:
    if value is None:
        return "待确认"
    return f"{value:g} 年"


def _bullet_lines(items: list[str], empty_text: str) -> list[str]:
    values = [item for item in items if item]
    if not values:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in values]


def _numbered_lines(items: list[str], empty_text: str) -> list[str]:
    values = [item for item in items if item]
    if not values:
        return [f"1. {empty_text}"]
    return [f"{index}. {item}" for index, item in enumerate(values, start=1)]


def _highlight_items(
    candidate: Candidate,
    match: CandidateMatch,
    explanations: list[CandidateMatchExplanation],
) -> list[str]:
    items: list[str] = []
    if candidate.skills:
        items.append(f"技能关键词：{', '.join(candidate.skills[:8])}")
    for explanation in explanations:
        if explanation.dimension in {"核心技能匹配", "项目经验匹配"} and explanation.conclusion:
            items.append(explanation.conclusion)
    return items or match.matched_points[:2]


def _project_and_certificate_items(candidate: Candidate) -> list[str]:
    items: list[str] = []
    for project in candidate.project_experiences[:3]:
        if isinstance(project, dict):
            name = project.get("name") or "项目经历"
            description = project.get("description") or project.get("raw") or ""
            items.append(f"{name}：{description}".rstrip("："))
    for certificate in candidate.certifications[:5]:
        items.append(f"证书：{certificate}")
    return items
