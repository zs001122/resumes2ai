# V2 验收说明

本文档用于 V2 收缩后的交付验收，覆盖 V2.1.2 功能截止版本的端到端链路和 MVP 主流程回归。

> 收缩说明：本文档是 V2 稳定化验收与交付检查的唯一执行入口，不再承接新功能规划。V2 完成范围、冻结边界和下一大版本候选池以 [V2_STATUS_AND_ROADMAP.md](./V2_STATUS_AND_ROADMAP.md) 为准。

## 1. 启动服务

推荐一键启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-dev.ps1
```

该脚本会自动补齐本地 env、执行迁移并同时启动前后端。按 `Ctrl+C` 可停止服务。

也可以分别启动。

后端：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8010
```

前端：

```powershell
cd frontend
npm run dev
```

默认访问：

- 前端：http://localhost:3000
- 后端：http://localhost:8010

## 2. 自动验收脚本

在项目根目录运行：

```powershell
python scripts/api_tests/06_v2_acceptance.py
```

脚本会自动创建岗位、生成两份 TXT 简历样例、上传一份损坏 PDF 作为失败样例，并验证：

- `/api/dashboard` 工作台汇总可访问。
- 岗位创建、复制、暂停、重新开放、关闭可用。
- 批量上传后可查看每份简历的上传、解析和评分状态。
- 失败解析任务可重试；如果重试后解析成功，必须继续生成评分结果。
- 候选人列表支持组合筛选。
- 批量状态更新遇到不存在候选人时返回部分完成结果。
- 候选人详情相关的匹配解释、备注和时间线可访问。
- 候选人可加入人才库，并支持标签和跨岗位搜索。
- 岗位漏斗统计和 JD 质量检查可访问。
- 岗位上下文接口会拒绝跨岗位候选人的状态、评分、备注、时间线和人才库入库操作。
- 开放和暂停岗位可编辑，关闭岗位禁止编辑且不能重新开放。

## 2.1 自动验证命令

最近一次本地完整验证日期：2026-05-29。

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests scripts
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern

cd ..\frontend
npm run lint
npm run build
```

当前记录结果：

- 后端 pytest：通过，`13 passed`。
- 后端 ruff：通过。
- 真实样本解析与匹配诊断：通过，`.doc` 明确记录为暂不支持，DOCX / PDF 样本正常输出解析和匹配结果。
- 前端 lint：通过。
- 前端生产构建：通过。
- Alembic 当前版本：`20260521_0010 (head)`。
- 一键启动脚本语法检查：通过，`scripts\run-dev.ps1` 可解析。

## 2.2 演示数据与环境重置

API 验收脚本可创建演示数据：

```powershell
python scripts/api_tests/06_v2_acceptance.py
```

清理本地演示数据前先预览：

```powershell
python scripts/api_tests/08_clear_all.py
```

确认清空数据库记录和 uploads 文件：

```powershell
python scripts/api_tests/08_clear_all.py --yes
```

只清空数据库、保留 uploads 文件：

```powershell
python scripts/api_tests/08_clear_all.py --yes --keep-files
```

## 3. 手动验收路径

1. 进入 `/dashboard`，确认待办、异常和最近活动可见。
2. 创建一个岗位，确认 JD 解析、保存和岗位列表展示正常。
3. 在岗位详情页上传多份简历，进入上传队列查看每份文件状态。
4. 上传一个损坏 PDF，确认失败原因和重试入口可见。
5. 进入候选人列表，组合使用状态、分数、城市、技能、风险和低置信度筛选。
6. 勾选多个候选人执行批量状态更新、批量入库和批量重新评分，确认完成或部分完成提示可见。
7. 进入候选人详情，确认分项评分、解释、证据、原文高亮、备注和时间线可见。
8. 将候选人加入人才库，进入 `/talent-pool` 用关键词或技能搜索。
9. 回到岗位详情，检查漏斗统计、JD 质量提示、复制、暂停、重开和关闭。
10. 创建两个岗位并分别上传候选人，确认岗位 A 不能操作岗位 B 的候选人。

## 4. 合规与回归检查

- 自动评分只使用岗位相关能力、经历、技能、教育和项目字段；手机号、邮箱等联系方式不参与匹配判断。
- 简历结构化抽取规则层必须优先保留手机号、邮箱、明确键值对、日期区间和学校/公司归一化；AI 只作为职责、技能熟练度、项目和自由文本的兜底增强。
- 风险提示必须使用“待确认”或“建议复核”语气。
- 关键人工操作需要写入时间线，包括字段修正、备注、状态变更、批量操作和人才库流转。
- 候选人状态、评分、备注和时间线必须基于真实岗位关联。
- 人才库可跨岗位搜索，但指定岗位入库时必须绑定候选人的真实岗位来源。
- `open`、`paused` 状态下岗位可编辑；`closed` 状态下岗位禁止编辑且不能重新开放。V2.1 / V2.1.1 已补充岗位标准版本和批量重评规则；V2.1.2 已补充重复候选人人工复核与风险收口。
- MVP 主流程仍需可用：创建岗位、上传简历、解析结构化字段、生成匹配结果、候选人状态流转。

## 5. 验收结果

V2 当前通过以下检查：

- 后端 `compileall`
- 后端 `ruff check`
- 前端 `npm run build`
- V2 TestClient 验收测试 `backend/tests/test_v2_acceptance.py`

截至 2026-05-29，自动化验收未发现阻断缺陷。当前剩余工作是手动 UI 验收：

- 使用 `scripts\run-dev.ps1` 启动前后端。
- 按第 3 节手动路径完成主链路回归。
- 如发现阻断演示、上传、解析、评分、候选人操作或启动的问题，只做缺陷修复，不扩大 V2 功能范围。

## 6. V2 已知限制

以下不是 V2 缺陷，已归入下一大版本候选池或后续大版本：

- 不保存推荐报告历史。
- 不导出 PDF / Word 推荐报告。
- 不支持文本粘贴录入简历。
- 不支持 ZIP 批量上传。
- 不引入后台异步任务队列。
- 不升级 AI 分项解释为完整 AI JSON 解释链路。
- 不做自动合并重复候选人。
- 不做候选人主档案合并。
- 不引入多岗位归属模型。
- 不做复杂权限、审批、面试日程、通知、ATS、Offer、招聘大屏和图片 OCR。

## 6.1 AI 解析开关

AI 简历结构化增强默认关闭，避免本地验收依赖外部网络或模型稳定性。需要启用时，在 `backend/.env` 中设置：

```text
AI_RESUME_PARSE_ENABLED=true
```

启用后，规则层仍优先保护手机号、邮箱、明确键值对、日期区间工作年限和学校/公司归一化；AI 只补全职责总结、技能熟练度、自由文本项目描述和中英文混合文本。

## 7. V2 冻结规则

V2 冻结后只允许：

- 阻断验收的 bug 修复。
- 验收脚本、清理脚本和文档补齐。
- 启动、迁移、演示数据和本地开发体验修正。
- 不改变业务范围的小 UI 文案、状态展示和错误提示修正。

V2 冻结后禁止：

- 新业务功能。
- 新数据模型。
- 新上传入口或上传形态。
- 新导出形态。
- 新后台任务架构。
- 候选人主档案合并、自动合并、多岗位归属。

## 8. V2 状态总览与后续入口

当前 V2 / V2.1 / V2.1.1 / V2.1.2 的完成状态、未完成事项和后续路线图见：

```text
docs/V2_STATUS_AND_ROADMAP.md
```

V2.1.2 是 V2 功能截止版本。V2 后续只做稳定化、验收和交付，不再新增 V2.1.x 功能；新业务能力进入下一大版本候选池。

历史任务拆解仍可按需追溯：

```text
docs/V2_TASK_BREAKDOWN.md
docs/V2_1_TASK_BREAKDOWN.md
docs/V2_1_1_TASK_BREAKDOWN.md
docs/V2_ISSUE_FIX_PLAN.md
```

V2.1.1 第一版已补充以下验收项：

- 岗位编辑页：开放和暂停岗位可编辑，关闭岗位不可编辑。
- 标准版本：修改标准字段生成新版本，修改非标准字段不生成新版本。
- 批量重新评分：岗位标准变更后可对历史候选人按最新标准重新评分。
- 评分追溯：新匹配结果关联最新 `job_standard_version_id`。
- 重试一致性：重新解析和上传任务重试成功后仍执行重复候选人识别。
- 自动化检查：后端测试、后端 lint、前端构建和前端 lint 均可非交互执行。

V2.1.2 第一版已补充以下验收项：

- 重复复核状态：疑似重复记录支持待复核、已忽略、确认重复三种状态。
- 候选人详情：重复识别卡片展示复核状态，并允许 HR 忽略风险或确认重复。
- 工作台待办：待复核重复风险进入今日待处理和异常概览，待办链接直达候选人详情。
- 上传队列：重复列展示待复核、已忽略和确认重复统计。
- 时间线追溯：重复复核动作写入候选人操作时间线。
- 边界约束：复核只记录人工判断，不自动合并候选人，不修改候选人主档案。

当前验证命令：

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests scripts
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern

cd ..\frontend
npm run lint
npm run build
```
