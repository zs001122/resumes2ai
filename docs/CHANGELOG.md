# 开发记录

本文档按时间追加项目关键开发、实验、修复和文档重构记录。它不是完整 git log，而是便于后续回顾决策背景、验收结果和遗留问题的开发日志。

## 2026-07-15 - 真实样本脱敏 fixture 固化

Branch: `experiment/resume-parse-vnext`
Commit: 本提交

背景：

`export_resume_parse_fixture.py --redact` 已经具备真实 PDF 脱敏导出能力，需要把当前 `test_data/` 中两份真实样本固化为可提交的 parser regression fixtures，覆盖导出型 PDF 和项目密集型简历。

变更：

- 新增 `real_pdf_python_ai` 脱敏 fixture，覆盖姓名、联系方式、教育、单条工作经历和多项目经历。
- 新增 `real_pdf_exported_boss` 脱敏 fixture，覆盖导出型 PDF 的无标题姓名、联系方式后置、教育恢复、work company 继承和项目切分。
- 在固化前额外脱敏真实姓名、手机号、邮箱、学校、公司和客户组织名称。

验收：

- 敏感词扫描：未命中原始姓名、手机号、邮箱、学校、公司和客户组织名称。
- `./venv/bin/python -m pytest tests/test_resume_parser_vnext.py -q`：9 passed。

遗留问题：

- 仍需继续收集更多招聘平台和不同版式 PDF/DOCX 样本。
- 脱敏 fixture 仍需人工复核，确认项目内容不包含业务敏感信息。

下一步：

- 继续观察真实上传样本，按 fixture-first 方式修 parser 新错例。

## 2026-07-06 - 真实样本回归入口和证据页体验优化

Branch: `experiment/resume-parse-vnext`
Commit: `effc841`

背景：

质量门禁和文档状态同步后，下一步进入真实样本回归 fixture 扩充和证据页体验优化。现有 `test_data/` 为本地真实 PDF，不适合直接提交原文，需要先提供脱敏导出入口；修正页候选证据也需要更便于 HR 快速判断。

变更：

- `export_resume_parse_fixture.py` 新增 `--redact`，导出前脱敏姓名、手机号、邮箱，并重新解析脱敏文本生成 expected JSON。
- 脱敏导出会同步处理 `--raw-exclude` 参数，避免 expected JSON 写入原始联系方式。
- 新增导出脚本脱敏 helper 测试。
- 修正页候选证据支持展开/收起、复制证据、定位证据。
- extractor 和 rejection_reason 在修正页转为 HR 更容易理解的文案。

验收：

- `./venv/bin/python -m pytest -q`：27 passed，1 warning。
- `./venv/bin/ruff check app tests scripts`：通过。
- `npm run lint`：通过。
- `npm run build`：通过。
- `--redact` 对真实 Case B PDF 试跑成功，输出到 `/tmp/resume_parse_fixture_redacted`；原始手机号检查无命中。

遗留问题：

- 脱敏导出仍需要人工复核 expected JSON，确认字段断言和原文片段不会泄露真实个人信息。
- 原文高亮仍主要依赖 source_text 精确匹配，后续可继续增强空白归一和片段定位。

下一步：

- 基于脱敏导出结果挑选 1-2 个真实样本固化为 repo fixture。
- 继续优化低置信字段汇总文案和详情页/修正页证据口径一致性。

## 2026-07-06 - 质量门禁和文档状态同步

Branch: `experiment/resume-parse-vnext`
Commit: `effc841`

背景：

vNext 0.4、correction feedback 和企业 ATS 风格 UI 已经完成并提交，但 ROADMAP、BACKLOG 和模块文档中仍有部分下一步状态停留在旧阶段；同时全量 ruff 增加 scripts 检查后，fixture 导出脚本存在 E402 门禁问题。

变更：

- 修复 `backend/scripts/export_resume_parse_fixture.py` 的 ruff E402 问题，保留 CLI 直接运行能力。
- 同步 ROADMAP、BACKLOG、parser、frontend、backend 和 testing 模块文档到当前真实开发状态。
- 将下一阶段收敛为真实样本 regression fixture 扩充和 evidence display 体验优化。

验收：

- `./venv/bin/python -m pytest -q`：24 passed，1 warning。
- `./venv/bin/ruff check app tests scripts`：通过。
- `npm run lint`：通过。
- `npm run build`：通过。

遗留问题：

- 下一阶段仍需要继续补真实脱敏样本，并把人工修正结果半自动沉淀为 parser regression fixture。

下一步：

- 进入真实样本回归 fixture 扩充和证据页体验优化。

## 2026-07-06 - 企业 ATS 风格 UI 优化

Branch: `experiment/resume-parse-vnext`
Commit: `6340bc7`

背景：

现有前端页面可用但视觉风格不够接近企业 ATS，用户要求在不新增业务功能的前提下优化 UI 风格。

变更：

- 首页、工作台、岗位列表、候选人修正页调整为更克制的信息密度和企业 ATS 风格。
- 统一页面背景、顶部导航、状态色、表格和表单控件的视觉层级。
- 保留现有页面路由和业务逻辑，不新增 V2 业务入口。

验收：

- `npm run lint`：通过。
- `npm run build`：通过。

遗留问题：

- 证据区 source text 的折叠、定位和低置信原因表达仍需要继续优化。

下一步：

- 进入真实样本回归 fixture 扩充和证据页体验优化。

## 2026-07-03 - correction feedback loop

Branch: `experiment/resume-parse-vnext`
Commit: `93b9d9d`

背景：

vNext 0.4 已完成 Case B 的姓名、教育、work company 和 project 串联修复。下一步需要把 HR 在修正页套用 vNext 候选的动作沉淀到 correction log，并提供轻量方式把真实样本转成 parser regression fixture。

变更：

- 修正页保存时提交 `correction_sources`，只包含仍保持候选值的字段。
- 用户手动编辑字段时会清除该字段的 vNext 套用痕迹，避免误标来源。
- 后端不改数据库结构，复用 `FieldCorrectionLog.editor_id` 记录来源：`local` 或 `vnext:<extractor>@<confidence>`。
- 修改记录 UI 展示“来自 vNext 候选”徽标。
- 新增 `backend/scripts/export_resume_parse_fixture.py`，可从 PDF/DOCX/TXT 导出 vNext fixture 的 `.txt` 和 `.expected.json`。

验收：

- 新增后端测试覆盖 correction log 的 vNext 来源记录。
- `./venv/bin/python -m pytest -q`：24 passed，1 warning。
- `npm run lint`：通过。
- `./venv/bin/python scripts/export_resume_parse_fixture.py ...`：真实 Case B 试跑成功，输出 expected JSON 覆盖 name、education、work/project count 和 raw exclude。

遗留问题：

- correction log 仍是字段级来源记录，尚未把人工修正自动转成 fixture，需要人工执行导出脚本并补关键断言。

下一步：

- 用真实样本或修正结果跑一次 fixture 导出脚本，并补充到 parser regression。

## 2026-07-03 - resume parser vNext 0.4 project item normalization

Branch: `experiment/resume-parse-vnext`
Commit: `2aadf9c`

背景：

导出型 PDF 会出现连续两个项目标题，随后才出现两个 `项目描述` 块的布局。旧逻辑会让前一个项目只剩标题，后一个项目吞掉两个描述块，导致项目 raw 互相串。

变更：

- 在 project chunks 层新增错位归一化：当前 chunk 是项目标题且下一 chunk 是项目标题 + 多个项目描述块时，把第一个描述块回填给前一个标题。
- 保留后一个项目标题，并只让它承接后续描述块，避免多个项目 raw 互相串。
- 新增 `exported_pdf_project_order` fixture，断言智能体项目和招标项目各自只包含自己的描述，不包含对方描述。
- vNext 测试增加 `project_expectations`，支持按项目名检查 raw contains / excludes。

验收：

- `./venv/bin/python -m pytest tests/test_resume_parser_vnext.py -q`：7 passed。
- `./venv/bin/python -m pytest -q`：23 passed，1 warning。
- `./venv/bin/ruff check app tests`：通过。
- `git diff --check`：通过。
- 真实 Case B 复跑：`AI能力开发平台` raw 只含 AI 平台描述，不含招标描述；`招标书信息采集工具开发` raw 只含招标描述，不含 AI 平台描述；low confidence 和 warnings 为空。

遗留问题：

- 仍需更多真实脱敏样本覆盖不同 PDF 导出布局。
- 人工修正反馈还没有转成 parser regression fixture。

下一步：

- 优先进入 correction feedback，或继续补真实样本 regression fixtures。

## 2026-07-03 - resume parser vNext 0.4 work normalization

Branch: `experiment/resume-parse-vnext`
Commit: `2aadf9c`

背景：

Case B 在 name 和 education 恢复后，仍存在一条有岗位和时间但缺 company 的工作经历；同时 project raw / block 可能混入联系方式、姓名和教育行，影响 HR 看证据。

变更：

- work normalization：当后续 work item 缺 company 但有岗位或时间时，继承上一条明确公司。
- title 识别优先级调整：优先识别 `工程师`、`分析师` 等职位，避免把业务方向如“智能体开发”误当岗位。
- work/project raw 去污染：遇到联系方式、求职意向、工作经验、学校+学历+时间行时截断经验条目。
- section boundary 同步收紧：project/work 遇到联系方式切到 profile，遇到学校+学历+时间切到 education。
- vNext fixture 增加 `work_companies`、`work_titles` 和 `project_raw_excludes` 断言。

验收：

- `./venv/bin/python -m pytest tests/test_resume_parser_vnext.py -q`：6 passed。
- `./venv/bin/python -m pytest -q`：22 passed，1 warning。
- `./venv/bin/ruff check app tests`：通过。
- `git diff --check`：通过。
- 真实 Case B 复跑：第二条 work 继承 `广州智算信息技术有限公司`，title 为 `算法工程师`；project raw 和 project block 不再包含手机号、姓名、学校；low confidence 和 warnings 为空。

遗留问题：

- 导出型 PDF 的项目标题和项目描述仍可能顺序错位，需要后续 project item normalization。
- 人工修正反馈还没有转成 parser regression fixture。

下一步：

- 进入 project item normalization 或 correction feedback，优先级按下一轮真实样本观察决定。

## 2026-07-02 - resume parser vNext 0.4 fallback and confidence policy

Branch: `experiment/resume-parse-vnext`
Commit: `2aadf9c`

背景：

用户确认 parser 模块继续优化四项质量问题：无标签姓名、无标题教育、工作/项目证据过长、核心字段和可选字段低置信策略混在一起。

变更：

- parser 版本升级为 `resume-parser-vnext-0.4`。
- basics fallback：从简历头部无标签姓名行恢复候选人姓名，并支持在联系方式/人口信息行后恢复后置姓名，覆盖导出型 PDF 或文件名不可用场景。
- education recovery：无 `教育经历` 标题时，在 1-3 行窗口内组合时间、学校、学历和专业恢复教育经历；候选按教育信号、证据长度和噪声排序，避免项目/岗位文本污染教育 source text。
- item-level evidence：为 work/project 生成 item 级候选 extractor，并把 source text 控制在 260 字以内。
- confidence policy：低置信字段改为核心字段优先，`certifications` 等可选字段缺失不再进入低置信列表或质量扣分。
- 新增 `exported_pdf_layout`、`exported_pdf_contact_name` vNext fixtures。

验收：

- `./venv/bin/python -m pytest tests/test_resume_parser_vnext.py -q`：6 passed。
- `./venv/bin/python -m pytest -q`：22 passed，1 warning。
- `./venv/bin/ruff check app tests`：通过。
- 真实样本复跑：`杨梓灼（python后端、AI应用开发）.pdf` 和 `直聘简历-未命名 (1).pdf` 均生成 `resume-parser-vnext-0.4`；Case B 恢复 `name=吴树锌`、`education=韶关学院/本科/信息与计算科学/2019-2023`，低置信字段和 warnings 为空。

遗留问题：

- 有岗位和时间但缺 company 的 work item 仍需要后续 normalization。
- work/project raw 仍可能受联系方式或相邻 section 污染，需要继续缩短并归一化证据。
- 人工修正反馈还没有转成 parser regression fixture。

下一步：

- 进入 work normalization，优先处理缺 company 但有岗位和时间的工作经历。
- 把真实样本缺陷继续补成 parser regression fixture。

## 2026-07-02 - 文档结构重构为路线、记录和模块文档

Branch: `experiment/resume-parse-vnext`
Commit: `ac8f8da`

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
