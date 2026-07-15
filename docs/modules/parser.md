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

### vNext 0.4

- basics fallback：支持无 `姓名` 标签、导出型 PDF、文件名不可用时，从简历头部无标签姓名行恢复候选人姓名。
- education recovery：无 `教育经历` 标题时，支持在 1-3 行窗口内组合时间、学校、学历和专业恢复教育经历。
- item-level evidence：为 work/project 生成 `section:work:item:rules` 和 `section:projects:item:rules` 候选，source text 控制在 260 字以内。
- confidence policy：低置信字段按核心字段优先，`certifications` 等可选增强字段不再因缺失进入低置信列表或质量扣分。
- work normalization：有岗位和时间但缺 company 的工作经历会继承相邻明确公司，减少导出型 PDF 拆行导致的结构缺口。
- work/project raw 去污染：截断联系方式、求职意向、学校/学历/时间等相邻 section 噪声。
- project item normalization：修复导出型 PDF 中连续项目标题和项目描述错位导致的 raw 串联。
- correction feedback：修正页套用 vNext 候选后，correction log 复用 `editor_id` 记录 `vnext:<extractor>@<confidence>` 来源。
- 新增 `exported_pdf_layout`、`exported_pdf_contact_name` 和 `exported_pdf_project_order` fixtures，覆盖导出型 PDF 布局、无标签姓名、多行无标题教育、联系方式后置姓名、item evidence 和项目描述错位。

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

1. Case A work description 仍可能偏长；vNext 0.4 已生成 item-level source text，但项目条目证据还需继续观察 HR 是否容易判断。
2. Case B name、structured education、教育 source text、缺 company work item、联系方式/教育污染 project raw、项目标题/描述错位已在真实样本复跑中恢复。
3. correction feedback 已记录候选来源，但从人工修正结果到 parser regression fixture 仍需要人工执行导出脚本并补关键断言。
4. 已固化 `real_pdf_python_ai` 和 `real_pdf_exported_boss` 两组真实脱敏 fixture；仍需更多真实脱敏样本覆盖不同招聘平台、PDF 导出布局、项目密集型简历和非标准教育布局。

## 下一步计划

优先级从高到低：

1. 继续补真实脱敏样本回归，重点覆盖导出型 PDF、无标题教育、长工作/项目经历、联系方式后置布局和项目标题/描述错位。
2. 使用 `export_resume_parse_fixture.py` 把真实修正结果半自动沉淀为 fixture，并手工补充 name、education、work/project count、raw excludes 等关键断言。
3. evidence display：继续提高 source text 的 HR 可读性、低置信原因表达和原文定位稳定性。
4. 观察 Case A project item evidence，必要时继续细化项目条目摘要和 source text。

## 回归命令

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_resume_parser_vnext.py
.\venv\Scripts\python.exe -m pytest tests/test_v2_acceptance.py
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

## Fixture 生成

真实样本或人工修正结果需要固化为 parser regression 时，先导出文本和 expected JSON，再手工补充关键断言。真实 PDF/DOCX 优先使用 `--redact` 输出脱敏 fixture 草稿：

```powershell
cd backend
.\venv\Scripts\python.exe scripts\export_resume_parse_fixture.py `
  --input ..\test_data\sample.pdf `
  --case-name real_sample_case `
  --redact `
  --low-confidence-absent name `
  --low-confidence-absent education `
  --raw-exclude 手机号或不应串入项目的文本
```

导出后必须人工复核 `.txt` 和 `.expected.json`，确认脱敏文本仍能覆盖原错例，同时不包含真实联系方式。

## 维护规则

- parser 规则、prompt、fixtures、parse run 结构和真实样本缺陷记录在本文档。
- UI 证据展示记录在 `frontend.md`。
- parser 输出参与匹配的策略记录在 `matching.md`。
