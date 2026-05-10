from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.schemas.v2 import CandidateMatchExplanationCreate


def build_match_explanations(match: CandidateMatch, candidate: Candidate) -> list[CandidateMatchExplanationCreate]:
    skills = ", ".join(candidate.skills or []) or None
    return [
        CandidateMatchExplanationCreate(
            dimension="必备条件匹配",
            score=_dimension_score(match.score, 1.0),
            conclusion=match.matched_points[0] if match.matched_points else "候选人基础信息已完成解析，需继续复核岗位必备条件。",
            evidence_text=_first_text(match.matched_points) or skills,
            confidence=0.78,
        ),
        CandidateMatchExplanationCreate(
            dimension="核心技能匹配",
            score=_dimension_score(match.score, 1.05),
            conclusion=f"候选人技能关键词：{skills}" if skills else "简历中暂未抽取到明确技能关键词。",
            evidence_text=skills,
            confidence=0.72 if skills else 0.35,
        ),
        CandidateMatchExplanationCreate(
            dimension="项目经验匹配",
            score=_dimension_score(match.score, 0.92),
            conclusion=_first_text(match.matched_points[1:]) or "项目经历需要结合原简历进一步复核。",
            evidence_text=_first_text(match.matched_points[1:]),
            confidence=0.64,
        ),
        CandidateMatchExplanationCreate(
            dimension="工作年限匹配",
            score=_years_score(candidate.years_of_experience),
            conclusion=(
                f"候选人解析工作年限为 {candidate.years_of_experience:g} 年。"
                if candidate.years_of_experience is not None
                else "工作年限未能稳定解析，建议 HR 复核。"
            ),
            evidence_text=str(candidate.years_of_experience) if candidate.years_of_experience is not None else None,
            confidence=0.7 if candidate.years_of_experience is not None else 0.3,
        ),
        CandidateMatchExplanationCreate(
            dimension="学历匹配",
            score=75 if candidate.highest_education else 45,
            conclusion=(
                f"候选人最高学历解析为 {candidate.highest_education}。"
                if candidate.highest_education
                else "最高学历暂未明确解析，建议 HR 复核。"
            ),
            evidence_text=candidate.highest_education,
            confidence=0.7 if candidate.highest_education else 0.3,
        ),
        CandidateMatchExplanationCreate(
            dimension="风险扣分",
            score=max(0, 100 - len(match.risks or []) * 15),
            conclusion=_first_text(match.risks) or "当前匹配结果未标记明确风险点。",
            evidence_text=_first_text(match.risks),
            confidence=0.68 if match.risks else 0.55,
        ),
    ]


def _dimension_score(score: float, multiplier: float) -> float:
    return round(max(0, min(100, score * multiplier)), 1)


def _years_score(years: float | None) -> float:
    if years is None:
        return 45
    return round(max(40, min(100, 50 + years * 8)), 1)


def _first_text(values: list[str] | None) -> str | None:
    if not values:
        return None
    return next((value for value in values if value), None)
