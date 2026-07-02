# 匹配评分模块文档

## 模块定位

匹配模块负责把岗位标准和候选人结构化字段转成分数、推荐等级、matched points、weak points 和推荐摘要。

当前原则：

- 不使用手机号、邮箱等联系方式参与评分。
- 风险提示使用“待确认”或“建议复核”语气。
- 低置信字段参与评分时应能解释其不确定性。
- 推荐摘要不保存历史，当前只支持 Markdown 生成、编辑、复制和下载。

## 已落地能力

- 本地兜底匹配从技能字面命中升级为分维度评分。
- 维度包括：必备技能、相关技能、项目证据、经验、学历、城市、排除项风险。
- 岗位族技能映射覆盖后端开发、前端开发、数据开发等方向。
- 输出 matched points / weak points。
- 匹配结果关联岗位标准版本。
- 岗位标准变更后可批量重新评分历史候选人。
- 推荐摘要 Markdown 可生成、编辑、复制和下载。

## 当前问题

- AI 分项解释尚未形成严格 JSON schema。
- 证据片段和维度评分的一致性还需加强。
- 低置信字段参与评分时，提示还不够细。
- 推荐摘要不保存历史，无法回看多轮编辑。

## 下一步候选

- AI JSON 分项解释结构化校验。
- evidence 与 score dimensions 对齐检查。
- 低置信字段参与评分时输出复核提示。
- 推荐报告历史保存进入下一大版本候选。
- PDF / Word 推荐报告导出进入下一大版本候选。

## 验收

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

重点检查：

- Java 后端候选人不只因 `SQL` 单词得分。
- Python/SQL 数据开发候选人对数据开发岗位明显高于不相关岗位。
- deal breaker 命中会扣分并产生 weak point。
- 推荐摘要不包含手机号、邮箱等敏感联系方式。

## 维护规则

- 评分维度、解释策略、推荐摘要策略记录在本文档。
- 候选人字段抽取质量问题记录在 `parser.md`。
- 推荐摘要 UI 体验记录在 `frontend.md`。
