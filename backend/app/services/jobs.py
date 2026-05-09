from app.schemas.job import JDParseRequest, JDParseResult


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
