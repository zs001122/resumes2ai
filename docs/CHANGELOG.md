# 开发记录

本文档按时间追加项目关键开发、实验、修复和文档重构记录。它不是完整 git log，而是便于后续回顾决策背景、验收结果和遗留问题的开发日志。

## 2026-07-02 - 文档结构重构为路线、记录和模块文档

Branch: `experiment/resume-parse-vnext`
Commit: pending

背景：

早期 MVP / V2 / V2.1 任务拆解、设计稿、验收说明和一次性 E2E 记录分散在 `docs/` 根目录。第一次收敛删除了重复入口，但同时弱化了长期主体路线和开发记忆。需要建立更适合后续持续迭代的文档结构。

变更：

- `README.md` 保留为项目入口。
- 新增 `docs/ROADMAP.md`，作为长期主体开发路线。
- 新增 `docs/CHANGELOG.md`，作为按轮追加的开发记录。
- 保留 `docs/BACKLOG.md`，作为待开发功能池。
- 新增 `docs/modules/`，拆分前端、后端、解析、匹配、测试、运维模块文档。
- 删除旧的 MVP / V2 阶段拆解、旧设计稿、旧验收说明和单次 E2E 文档；关键路线信息沉淀进 ROADMAP、CHANGELOG 和模块文档。

验收：

- 旧文档引用检查无残留。
- `git diff --check` 通过。
- 本轮仅改文档，未改代码，未跑业务测试。

遗留问题：

- 后续每轮开发结束后需要持续补充 CHANGELOG。
- 模块文档需要在后续开发中进一步补充接口、页面和测试细节。

下一步：

- 以 parser 模块为重点，进入 basics fallback、education recovery、item-level evidence 等下一轮解析质量增强。

## 2026-07-02 - resume parser vNext 0.3 section boundary

Branch: `experiment/resume-parse-vnext`
Commit: `ff4eba7`

背景：

真实简历样本显示 parser 的 section 边界存在污染：工作经历会吞掉“核心项目经历”，自我评价会继续吞后续公司/岗位/日期头。修正页虽然能看到 source text，但 evidence 过长且低置信判断不够可操作。

变更：

- 优化 `resume_sections.py` 的 section transition。
- `work` 遇到项目标题时切到 project。
- `self_evaluation` 遇到公司/日期/岗位头时切到 work。
- `split_section_items(lines, item_kind=...)` 区分 work 和 project，避免编号职责被误拆成多条工作经历。
- vNext parser 版本升级为 `resume-parser-vnext-0.3`。
- 增加 section 边界验收测试。

验收：

- 后端测试：`20 passed`。
- Ruff：通过。
- 两份真实脱敏简历重新 parse，均生成 `resume-parser-vnext-0.3`。
- 候选人详情页、修正页返回 200。

遗留问题：

- Case A work description 仍偏长。
- Case A project item source text 仍可能过长。
- Case B 仍缺 name 和 structured education。
- Case B 有一条 work item 缺 company。

下一步：

- basics fallback。
- education recovery。
- item-level evidence。
- low-confidence policy 分层。

## 2026-07-02 - vNext 真实样本 E2E 记录

Branch: `experiment/resume-parse-vnext`
Commit: `30389d1`

背景：

用户上传两份真实脱敏简历到 `test_data/`，需要走正常上传入口验证 vNext parse run、候选人详情证据区和修正页证据闭环。

变更：

- 通过正常上传 API 生成 parse run。
- 记录两份样本的 resume file、candidate、quality、low-confidence fields。
- 检查候选人详情页和修正页路由可访问。
- 记录 parser 缺陷清单。

验收：

- 两份样本 parse success。
- 候选人详情页和修正页返回 200。
- 证据区出现 `section:basics:rules`、`section:education:rules`、`section:work:rules`、`section:projects:rules` 等 extractor。

遗留问题：

- Work/project source text 过长。
- Case B name 和 education 缺失。
- `certifications` 等可选字段低置信提示偏强。

下一步：

- 优先修 section boundary。

## 2026-07-02 - 修正页接入 vNext 证据闭环

Branch: `experiment/resume-parse-vnext`
Commit: `a31ba22`

背景：

后端已经能产出 section candidates、低置信候选和 source text，候选人详情页也能查看证据。但人工修正页仍以旧字段为主，HR 难以基于候选和证据快速修正。

变更：

- 修正页拉取 `GET /api/resume-files/{resume_file_id}/parse-runs/latest`。
- 字段表单旁展示对应 field candidates。
- 低置信字段优先展开。
- 点击候选值可以填入表单。
- 展示 source text 作为证据。
- 没有 parse run 时降级为旧体验。

验收：

- 前端 lint 通过。
- 修正页能加载 parse run。
- 没有 parse run 时保持旧体验。

遗留问题：

- 点击证据高亮原文仍需继续优化稳定性。
- “来自 vNext 候选”的操作痕迹仍以 UI 状态为主，未改数据库结构。

下一步：

- 用真实简历走 E2E 验证候选证据是否足够 HR 使用。

## 2026-07-02 - vNext section evaluation loop

Branch: `experiment/resume-parse-vnext`
Commit: `1b6184a`

背景：

需要先建立小闭环：规则识别 section block，按 section prompt 抽结构化字段，候选写入 `ResumeFieldCandidate`，并有 fixtures 和 pytest 验证。

变更：

- 新增 section prompt 模板：basics、work、education、skills、projects。
- 新增 vNext section parser。
- 候选字段包含 extractor、confidence、source_text、rejection_reason。
- 新增解析评测 fixtures。
- 不接新业务入口，不改 V2 主流程。

验收：

- vNext parser 单测通过。
- V2 主链路不受影响。

遗留问题：

- field evidence 粒度还粗。
- 真实样本缺陷需要 E2E 验证后排序。

下一步：

- 接入候选人详情和修正页证据展示。

## 2026-07-02 - V2 收敛和一键启动整理

Branch: `experiment/resume-parse-vnext`
Commit: `ecdba8a`

背景：

V2 功能已覆盖可试用工作台主闭环，需要从持续扩展转为稳定化、验收和交付。

变更：

- 收敛 V2 边界。
- 补齐一键启动和本地运行说明。
- 明确 V2 不再新增新业务入口、新上传形态、新导出形态和后台任务架构。

验收：

- 启动和验收说明可用。
- V2 后续工作聚焦 bug 修复、验收和解析/匹配质量修复。

遗留问题：

- 历史任务文档需要进一步沉淀为长期 roadmap 和 changelog。

下一步：

- 建立长期文档体系和模块文档。
