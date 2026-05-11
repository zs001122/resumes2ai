from app.models.job import Job
from app.schemas.job import JDParseRequest, JDParseResult, JDQualityCheck


DEFAULT_SCORING_DIMENSIONS = ["技能匹配", "项目相关度", "经验年限", "行业经验"]


def parse_jd_locally(payload: JDParseRequest) -> JDParseResult:
    """Lightweight local parser used before the real AI provider is wired."""
    lines = [
        line.strip(" -、\t")
        for line in payload.jd.replace("\r\n", "\n").split("\n")
        if line.strip()
    ]

    responsibilities: list[str] = []
    must_have: list[str] = []
    nice_to_have: list[str] = []
    deal_breakers: list[str] = []

    current_bucket = must_have
    for line in lines:
        normalized = line.lower()
        if any(keyword in line for keyword in ["岗位职责", "工作职责", "职责描述"]):
            current_bucket = responsibilities
            continue
        if any(keyword in line for keyword in ["任职要求", "职位要求", "岗位要求"]):
            current_bucket = must_have
            continue
        if any(keyword in line for keyword in ["加分", "优先"]) or "nice to have" in normalized:
            current_bucket = nice_to_have
            if len(line) > 4:
                nice_to_have.append(line)
            continue
        if any(keyword in line for keyword in ["不接受", "必须", "硬性", "低于"]) and "不得" in line:
            deal_breakers.append(line)
            continue
        if any(keyword in normalized for keyword in ["responsibility", "responsibilities"]):
            current_bucket = responsibilities
            continue
        if any(keyword in normalized for keyword in ["requirement", "requirements"]):
            current_bucket = must_have
            continue
        current_bucket.append(line)

    if payload.experience_required:
        must_have.append(f"工作年限要求：{payload.experience_required}")
    if payload.education_required:
        must_have.append(f"学历要求：{payload.education_required}")

    return JDParseResult(
        responsibilities=_dedupe(responsibilities),
        must_have=_dedupe(must_have),
        nice_to_have=_dedupe(nice_to_have),
        deal_breakers=_dedupe(deal_breakers),
        scoring_dimensions=DEFAULT_SCORING_DIMENSIONS,
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def check_jd_quality(job: Job) -> JDQualityCheck:
    issues: list[str] = []
    suggestions: list[str] = []

    if len(job.jd.strip()) < 120:
        issues.append("JD 描述偏短，可能不足以支撑稳定筛选。")
        suggestions.append("补充岗位职责、核心要求、业务场景和团队背景。")
    if len(job.must_have or []) < 3:
        issues.append("必备条件不足，筛选标准可能过于宽泛。")
        suggestions.append("明确 3-6 条必须满足的能力或经验。")
    if not job.scoring_dimensions:
        issues.append("缺少评分维度，AI 匹配解释会不够稳定。")
        suggestions.append("至少保留技能匹配、项目相关度、经验年限等维度。")
    if not job.deal_breakers:
        suggestions.append("如有硬性排除条件，可补充为明确的复核规则。")
    if not job.experience_required:
        suggestions.append("建议明确工作年限要求，便于候选人排序。")
    if not job.education_required:
        suggestions.append("如学历是硬性要求，建议写入岗位基础信息。")

    score = 100 - len(issues) * 22 - max(0, len(suggestions) - 2) * 6
    return JDQualityCheck(score=max(0, min(100, score)), issues=issues, suggestions=suggestions)
