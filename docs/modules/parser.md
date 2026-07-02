# 简历解析模块文档

## 模块定位

解析模块负责从简历文件和文本中提取结构化候选人信息，并提供可复核的字段证据。

当前解析路线：

- 规则优先：手机号、邮箱、明确键值对、日期区间、学校/公司归一化。
- AI 兜底：职责总结、技能熟练度、工作/项目自由文本、中英文混合文本。
- vNext evidence：parse run、section blocks、field candidates、source text、confidence、rejection reason。

## 已落地能力

### 规则解析和真实样本修复

- `resume_sections.py` 集中维护 section alias、标题归一、嵌入标题拆分、工作/项目兜底推断和 section item 切分。
- `resume_parser.py` 接入 section 模块，修复年限来源优先级、无标题教育兜底、教育噪声过滤、工作经历 chunk 聚合、伪公司过滤、项目名称/角色/技术栈抽取和技能 alias 归一。
- 年限提取避免把毕业届别、年份、教育经历误算为工作经验。
- 工作经历避免把“完成信息”“用户身份认证信息”等职责短语误当公司。
- 技能 alias 覆盖 Spring Boot、RocketMQ、MyBatis-Plus、Vue3、ETL、数据仓库等。

当前样本回归基线：

```text
李浩斌 DOCX：years=0.2 edu=2 work=1 project=1
李浩斌 PDF ：years=0.2 edu=2 work=1 project=1
翁鑫源 DOCX：years=0.0 edu=2 work=1 project=3
翁鑫源 PDF ：years=0.0 edu=2 work=1 project=3
杨晓飞 DOCX：years=5.0 edu=3 work=3 project=5
杨晓飞 PDF ：years=5.0 edu=3 work=3 project=5
```

### vNext 0.2

- 新增 section prompt 模板：`basics.jinja`、`work.jinja`、`education.jinja`、`skills.jinja`、`projects.jinja`。
- 先规则识别 section block，再按 section prompt 抽结构化字段。
- 每个字段候选写入 `ResumeFieldCandidate`。
- 候选包含 `extractor`、`confidence`、`source_text`、`rejection_reason`。
- 新增解析评测 fixtures 和 pytest。
- 不接新业务入口，不改 V2 主流程。

### vNext 0.3

- `work` 遇到 `核心项目经历`、`核心项目`、`项目案例`、`代表项目` 等项目标题时切到 project。
- `self_evaluation` 遇到公司/日期/岗位头时切到 work。
- `project` 遇到明确公司/岗位头时可切回 work。
- `split_section_items(lines, item_kind=...)` 区分 work 和 project：project 可按编号项目标题拆分，work 不把编号职责误拆成多条经历。

## 真实样本 E2E

测试岗位：

- Job ID：`25eb00dc-aa93-45a6-b433-fff2b54238f6`
- 前端：`http://192.168.2.137:3010`
- 后端：`http://192.168.2.137:8010`

vNext 0.3 结果：

| Case | Latest candidate ID | Parser version | Quality | Work count | Project count | Result |
| --- | --- | --- | ---: | ---: | ---: | --- |
| A | `6c09ab77-a34f-4707-ae00-af993f0409d8` | `resume-parser-vnext-0.3` | 92 | 1 | 8 | `核心项目经历` 已拆到 project；work 不再把编号职责拆成多条经历。 |
| B | `7af68e6b-5b73-4eea-816d-04ff0dc5b254` | `resume-parser-vnext-0.3` | 68 | 2 | 4 | `self_evaluation` 已在后续公司/岗位头前停止；工作经历被恢复为 work rows。 |

## 当前缺陷清单

1. Case A work description 仍偏长，需要进一步把职责证据和项目证据拆短。
2. Case A project 已按编号拆分，但单个 project source text 仍可能过长。
3. Case B name 缺失，需要支持导出型 PDF 中无标签姓名识别。
4. Case B education 结构化缺失，需要支持无标题教育恢复。
5. Case B 有一条 work item 没有 company，需要后续 work normalization。
6. `certifications` 等可选字段低置信提示过强，应和核心必填字段区分。

## 下一步计划

优先级从高到低：

1. basics fallback：无标签姓名、导出型文件名、候选人名位置特征。
2. education recovery：学校 + 学历 + 专业 + 时间的无标题识别。
3. item-level evidence：缩短 work/project 的 source text。
4. confidence policy：核心字段和可选字段分层。
5. correction feedback：把人工修正动作转成 parser regression fixture。

## 回归命令

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_resume_parser_vnext.py
.\venv\Scripts\python.exe -m pytest tests/test_v2_acceptance.py
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

## 维护规则

- parser 规则、prompt、fixtures、parse run 结构和真实样本缺陷记录在本文档。
- UI 证据展示记录在 `frontend.md`。
- parser 输出参与匹配的策略记录在 `matching.md`。
