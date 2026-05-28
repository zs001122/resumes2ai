# 简历结构化提取与匹配优化实施方案

## 1. 文档定位

本文档记录基于真实样本目录 `D:\Desktop\1122\projects\resumes2ai\简历数据` 的诊断结果，并把后续优化落实为可实施、可验收的工程任务。

本方案属于 V2 稳定化阶段的缺陷修复，不新增独立业务模块，不改变岗位驱动的上传、解析、评分、复核主流程。

## 2. 诊断方式

已直接调用现有后端函数跑样本，而不是只看代码推断：

```text
ResumeTextExtractor.extract_text()
  -> parse_resume_text()
  -> _fallback_match()
```

使用的诊断岗位：

```text
岗位：软件开发实习生
地点：广州
经验：应届生或 1 年以内实习经验
学历：本科及以上
必备：Python、React、SQL
加分：FastAPI、Docker
排除：完全没有项目经验
```

样本覆盖：

- `.doc`：1 份
- `.docx`：4 份
- `.pdf`：5 份

## 3. 当前问题结论

### 3.1 文件提取

- 老 Word `.doc` 当前不支持，`刘杰忠 .doc` 报 `UnsupportedResumeFileType`。
- `.docx` 和 `.pdf` 都能提取文本，但同一候选人的两种格式在教育、工作、项目段落上的切分结果不一致。

### 3.2 年限提取

当前年限误判严重：

- `24年应届生` 被识别为 `24.0` 年经验。
- 文件名或正文中的 `2023` 被识别为 `2023.0` 年经验。
- 教育经历区间被纳入工作年限计算，例如 `2016-09 ~ 至今` 导致候选人被算成 `9.7` 年经验。
- 数据开发候选人的教育和工作区间混算后被识别为 `16.3` 年。
- 数据开发候选人简历头部明确写了 `7年工作经验`，但时间轴兜底曾从 `2016.10` 算到当前日期输出 `9.6` 年；这说明“可计算时间跨度”不能无条件高于候选人自述年限。

根因：

- `YEARS_RE` 对所有 `数字 + 年` 一视同仁。
- `_extract_years(source)` 使用全文，不区分文件名、教育段、工作段、项目段。
- `_years_from_date_ranges()` 对全文日期区间求最早开始和最晚结束，教育经历会污染工作经验。

### 3.3 段落边界

教育、工作、项目边界不稳定：

- “主修课程”“专业技能”被吞进教育经历。
- 有的 PDF 版本抽不到教育，但 DOCX 版本可以抽到。
- 工作经历中把“完成信息”“用户的身份认证信息”等动宾短语误当公司。
- 项目经历在部分样本中可以抽到，在部分样本中整个项目段落为空。

根因：

- `_extract_sections()` 只按有限标题切段，缺少二级标题和 stop title。
- `_extract_education()` 对教育段内每一行都生成记录，未过滤课程行、技能标题行和无学校/学历/时间的噪声行。
- `_extract_work_experiences()` 对每一行独立猜 company/title，缺少“日期行作为经历头，后续行为描述”的聚合逻辑。

### 3.4 技能提取

当前技能主要靠固定关键词命中：

- 能识别 Java、Vue、Spring、MySQL、Redis、Linux、Docker、SQL、Git、Nginx 等显式词。
- 缺少同义词和岗位族归并，例如 `SpringBoot`、`Spring Cloud`、`Mybatis-Plus`、`RocketMQ`、`ElasticSearch`、`ETL`、`数据仓库` 等不能稳定转成结构化技能标签。
- 技能没有熟练度、来源段落和项目证据强度。

### 3.5 匹配评分

本地兜底匹配 `_fallback_match()` 区分度不足：

- 只判断 `candidate.skills` 是否字面包含在 `job.must_have` 文本中。
- Java 后端候选人即使有 Spring/MySQL/Redis/Docker 项目，也因为岗位 must_have 是 Python/React/SQL，最后只命中 SQL。
- 多个候选人分数集中在 `70`，无法体现项目证据、岗位族匹配、经验风险和学历达标差异。

## 4. 修复目标

第一轮优化目标：

- 年限不再把毕业届别、年份、教育经历误算为工作经验。
- 教育、工作、项目段落能在当前样本上稳定分离。
- 工作经历不再把普通描述短语误识别为公司。
- 项目经历和项目技术栈能进入匹配输入。
- 本地兜底匹配从“技能字面命中”升级为分维度评分。
- 增加诊断脚本，后续每次改解析或匹配都能用同一批样本回归。

非目标：

- 不在本轮实现 `.doc` 原生解析；先在文档和错误提示中明确限制。后续可评估 LibreOffice 或 antiword 转换。
- 不引入新的异步任务队列。
- 不改变数据库模型。
- 不把匹配逻辑做成完整 ATS 规则引擎。

## 5. 具体实现任务

### 5.1 年限提取重构

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- 新增 `_extract_years(file_name, sections, source)`，替代当前全文 `_extract_years(source)`。
- 年限来源优先级：
  1. 简历头部或文件名中明确的 `7年工作经验`、`2年`、`3.5年`，但排除 `24年应届生`、`23届`、`2024届`。
  2. 工作经历 section 内的日期区间，作为没有明确自述年限时的兜底。
  3. 项目经历 section 内的日期区间作为补充，但不超过岗位经验上限判断时的主经验。
  4. 没有明确工作经历且出现 `应届`、`实习生` 时返回 `0`。
- 新增毕业届别和年份过滤：
  - `24年应届生`
  - `2024届`
  - 单独年份 `2023`
  - 年龄、手机号、邮箱数字
- `_years_from_date_ranges()` 只接收目标段落，不再对全文求最早和最晚。
- 对“至今”使用当前日期计算，但仅当区间来自工作/项目段。
- 如果头部明确年限和时间轴推算冲突，优先采用头部明确年限，并将时间轴结果作为可解释兜底或复核参考。

验收标准：

- 刘杰忠、李浩斌、翁鑫源的 `24年应届生` 不再输出 `24.0`。
- 李浩斌不再输出 `2023.0`。
- 王文辉不再因教育经历输出 `9.7`。
- 杨晓飞 DOCX / PDF 中的 `7年工作经验` 应优先于时间轴推算，输出 `7.0`，不能输出 `9.6`。
- 应届生或无明确工作经历候选人输出 `0` 或低置信 `None`，由业务决定最终展示。

### 5.2 section 切分增强

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- 扩展 `SECTION_ALIASES`：
  - 技能：`专业技能`、`技能清单`、`技能特长`
  - 求职意向：`求职意向`
  - 基本信息：`基本信息`、`个人信息`
  - 校园/获奖：`校园经历`、`荣誉证书`
- 新增 `STOP_SECTION_TITLES`，教育段遇到以下标题立即停止：
  - `主修课程`
  - `专业技能`
  - `个人优势`
  - `项目经历`
  - `实习经历`
  - `工作经历`
- `_extract_sections()` 保留段落来源，后续字段来源能指向正确 section。
- `_meaningful_lines()` 过滤纯标题行、课程说明行和明显装饰符号行。

验收标准：

- 王文辉教育经历不再包含“主修课程”和“专业技能”伪记录。
- 李浩斌 PDF 能识别出广州大学教育信息，或将教育字段标为低置信而不是生成噪声记录。
- 翁鑫源项目经历仍保留，教育缺失应明确进入低置信字段。

### 5.3 教育提取规则优化

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- `_extract_education()` 只保留满足以下任一条件的行：
  - 包含学校关键词：`大学`、`学院`、`学校`
  - 包含学历关键词且包含日期区间
  - 包含学校 + 学历 + 专业中的至少两个要素
- 对 `主修课程：...` 行不生成 education item，可作为教育描述保留到 `raw_detail`，本轮可先跳过。
- 专业识别增加常见专业关键词：
  - `计算机`
  - `软件`
  - `网络`
  - `电子信息`
  - `数据`
  - `通信`
- 最高学历不再用全文第一个关键词，改为按学历等级排序：
  - 博士 > 硕士/研究生 > 本科 > 大专/专科

验收标准：

- 王文辉只保留广东技术职业学院、广东工业大学两条教育记录。
- 刘杰忠保留专科和本科两条教育记录。
- 杨晓飞 DOCX 保留广西工业职业技术学院教育记录。

### 5.4 工作经历聚合与公司过滤

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- `_extract_work_experiences()` 从“逐行生成 item”改为“按日期行/公司行聚合 chunk”。
- 日期行或公司行作为经历头，后续无日期的描述行合并到当前经历 `description`。
- 公司识别增加负面过滤：
  - 以 `完成`、`使用`、`负责`、`协助`、`校验`、`管理` 开头的短语不作为公司。
  - 包含 `身份认证信息`、`建筑施工信息`、`实时更新设施信息` 等业务对象词时不作为公司。
- 对没有公司但有时间和岗位/项目职责的经历，保留为低置信工作经历，不伪造公司。

验收标准：

- 刘杰忠不再出现 `完成信息`、`用户的身份认证信息` 等公司。
- 刘杰忠实习经历应聚合为 1 条主经历，描述包含云桌面系统、Spring Security、Docker 等职责。
- 杨晓飞 PDF 工作经历能保留长城计算机软件与系统有限公司等公司信息。

### 5.5 项目经历和项目技术栈优化

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- `_split_section_items()` 支持以下项目起始模式：
  - 日期开头：`2022/03-2022/04`
  - 项目名 + 角色 + 日期
  - `项目名称：`
  - 项目符号 + 日期
- 项目 chunk 内识别：
  - `name`
  - `role`
  - `time_range`
  - `technologies`
  - `description`
- 技术栈从 `项目技术`、`技术栈`、`项目环境` 后的文本优先提取。

验收标准：

- 刘杰忠“本地生活服务站”项目保留为 1 条结构化项目，技术栈包含 Spring/MySQL/Redis/RocketMQ/Nginx/Docker。
- 翁鑫源 STM32 项目保留项目时间、项目名称和角色。
- 杨晓飞 PDF 至少保留市场监管数据治理项目，职责描述不丢失。

### 5.6 技能词库和归一化

影响文件：

- `backend/app/services/resume_parser.py`

实现内容：

- 增加 `SKILL_ALIASES`：
  - `SpringBoot` -> `Spring Boot`
  - `SpringCloud` -> `Spring Cloud`
  - `Mybatis-Plus` -> `MyBatis-Plus`
  - `Rocketmq` -> `RocketMQ`
  - `elasticsearch` -> `ElasticSearch`
  - `mysql` -> `MySQL`
  - `vue3` -> `Vue`
  - `element-plus` -> `Element Plus`
  - `etl` -> `ETL`
- `_extract_skills()` 返回归一化后的去重技能。
- 第一轮仍保持 `list[str]`，不改变数据库结构；熟练度先保留在 AI 增强字段和原文证据里。

验收标准：

- 刘杰忠项目技术栈能提取 RocketMQ、ElasticSearch、MyBatis-Plus。
- 杨晓飞能提取 ETL、数据仓库相关关键词。
- Vue3、vue、Vue 归一为 Vue。

### 5.7 本地匹配兜底重构

影响文件：

- `backend/app/services/matching.py`

实现内容：

- 新增分维度评分函数：
  - `_score_required_skills(job, candidate)`
  - `_score_related_skills(job, candidate)`
  - `_score_project_evidence(job, candidate)`
  - `_score_experience(job, candidate)`
  - `_score_education(job, candidate)`
  - `_score_location(job, candidate)`
  - `_score_deal_breakers(job, candidate)`
- 新增岗位族技能映射：
  - 后端开发：Java、Spring、Spring Boot、MySQL、Redis、Linux、Docker、Nginx、SQL
  - 前端开发：JavaScript、TypeScript、React、Vue、Element Plus
  - 数据开发：Python、SQL、MySQL、ETL、数据仓库、Excel
- 分数建议：
  - 必备技能直接命中：30 分
  - 同类技能/岗位族证据：20 分
  - 项目证据：20 分
  - 经验匹配：10 分
  - 学历匹配：10 分
  - 城市/到岗匹配：5 分
  - 风险扣分：最多 -20 分
- `matched_points` 输出证据，例如：
  - `项目中使用 Spring Boot、Redis、Docker，具备后端开发相关项目证据`
  - `岗位要求 SQL，候选人技能和项目均出现 SQL/MySQL`
- `weak_points` 输出缺口，例如：
  - `岗位明确要求 React，但简历未体现 React 项目经验`
  - `工作年限来自低置信规则，需人工确认`

验收标准：

- Java 后端候选人不再只因为 `SQL` 一个词得分。
- Python/SQL 数据开发候选人对数据开发岗位应明显高于软件开发实习生岗位。
- 同一批样本的分数有区分度，不再集中固定在 `70`。

### 5.8 诊断脚本固化

新增文件：

- `backend/scripts/diagnose_resume_parse_match.py`

实现内容：

- 参数：
  - `--sample-dir`
  - `--job-profile software-intern|data-developer`
  - `--json`
- 输出字段：
  - 文件名
  - 后缀
  - 文本长度
  - 姓名
  - 年限
  - 最高学历
  - 教育数量
  - 工作数量
  - 项目数量
  - 技能
  - 低置信字段
  - 匹配分
  - 推荐等级
  - 匹配点
  - 短板
  - 首条教育/工作/项目
- 遇到 `.doc` 不阻塞全量诊断，记录 error 并继续。

建议命令：

```powershell
cd backend
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

验收标准：

- 能完整跑完当前 `简历数据` 目录。
- 输出可用于改动前后对比。
- 后续解析和匹配改动必须先跑该脚本。

## 6. 实施顺序

建议按以下顺序实施：

1. 固化诊断脚本，保存当前基线。
2. 修复年限提取，避免最严重的误判。
3. 增强 section 切分和教育过滤。
4. 重构工作经历聚合和公司过滤。
5. 优化项目经历和技术栈提取。
6. 扩展技能词库和归一化。
7. 重构本地兜底匹配评分。
8. 补充单元测试和诊断脚本回归。
9. 跑后端 `py_compile`、`ruff`、`pytest`。
10. 更新验收文档和 README 状态。

## 7. 测试补强

建议新增或扩展测试：

- `backend/tests/test_resume_parser.py`
  - `24年应届生` 不计入经验。
  - 教育区间不计入工作经验。
  - 主修课程不生成教育记录。
  - 公司过滤不把动宾短语当公司。
  - 项目符号 + 日期能生成项目记录。
- `backend/tests/test_matching.py`
  - 必备技能直接命中得分。
  - 岗位族技能证据得分。
  - 项目证据得分。
  - 缺失核心技能生成 weak point。
  - deal breaker 命中扣分。

## 8. 验收标准

第一轮优化完成后，必须满足：

- 当前 `简历数据` 目录诊断脚本完整跑完。
- `.doc` 被明确记录为不支持，不影响其他文件。
- 年限字段不再出现 `24.0`、`2023.0` 这类明显错误。
- 简历头部明确写了 `X年工作经验` 时，诊断脚本结果应优先展示该值；例如杨晓飞样本应输出 `7.0`。
- 教育记录不包含主修课程和专业技能伪记录。
- 工作公司不包含“完成信息”“用户的身份认证信息”等误识别。
- 项目经历至少覆盖当前样本中明确存在的项目段。
- 匹配结果能解释直接命中、同类技能、项目证据和短板。
- 后端语法检查通过。
- 后端相关测试通过。

### 8.1 当前样本回归结果

本轮已在 `D:\Desktop\1122\projects\resumes2ai\简历数据` 上补充回归，新增验收点：

- `校园经历`、`校园活动`、`校内外实践活动` 作为独立 section 边界，不能继续拼到工作经历描述中。
- 带空格中文日期区间必须可解析，例如 `2023 年 09 月~2023 年 11 月`。
- 简历头部没有 `教育经历` 标题时，仍可从 `日期 + 学校 + 学历/专业` 行抽取教育，但不跨入项目/技能/校园活动段。

当前诊断基线：

```text
李浩斌 DOCX：years=0.2 edu=2 work=1 project=1
李浩斌 PDF ：years=0.2 edu=2 work=1 project=1
翁鑫源 DOCX：years=0.0 edu=2 work=1 project=3
翁鑫源 PDF ：years=0.0 edu=2 work=1 project=3
杨晓飞 DOCX：years=5.0 edu=3 work=3 project=5
杨晓飞 PDF ：years=5.0 edu=3 work=3 project=5
```

关键修复说明：

- 李浩斌此前 `years=2.9` 来自校园职务日期污染工作经历；当前工作经历只保留 `广州华资软件技术有限公司` 实习，年限来源为 `2023 年 09 月~2023 年 11 月`。
- 翁鑫源的在校项目仍进入项目经历，`广州小蚁智控科技有限公司 实习员工` 作为真实实习保留在工作经历。
- 翁鑫源教育因无标题漏抽的问题已通过头部教育兜底修复。
- 杨晓飞样本存在 `7年工作经验` 和 `5年数据开发经验` 两个证据；当前优先使用岗位方向更明确的 `5年数据开发经验`，避免匹配阶段把泛化总年限当成相关经验年限。

### 8.2 当前实现落地清单

本轮已经落地到代码的内容：

- `resume_sections.py`：集中维护 section alias、标题归一、嵌入标题拆分、工作/项目兜底推断和 section item 切分。
- `resume_parser.py`：接入 section 模块，修复年限来源优先级、无标题教育兜底、教育噪声过滤、工作经历 chunk 聚合、伪公司过滤、项目名称/角色/技术栈抽取和技能 alias 归一。
- `matching.py`：本地兜底匹配拆成必备技能、相关技能、项目证据、年限、学历、城市、排除项风险等维度，避免分数集中在固定 `70` 附近。
- `test_v2_acceptance.py`：补充空格标题、无标题 section、年限优先级、校园经历边界、中文日期区间、无标题教育等回归用例。
- `diagnose_resume_parse_match.py`：固化真实样本批量诊断入口，支持 `software-intern` 和 `data-developer` 两套岗位画像，并可输出 JSON。

当前仍保持为后续阶段的内容：

- `.doc` 原生解析或转换链路。
- 独立 contact / education / work / project / skill extractor 文件拆分。
- 字段级置信度模型和人工复核队列扩展。
- LLM evidence schema 强校验与非结构化摘要增强。

## 9. 风险与取舍

### 9.1 规则增强风险

规则越强，越可能过拟合当前样本。降低风险方式：

- 所有过滤规则必须可解释。
- 优先过滤明显噪声，不强行推断缺失字段。
- 低置信字段保留给人工复核，不伪造结构化结果。

### 9.2 AI 与规则合并风险

当前 `_merge_ai_payload()` 对部分字段只在规则为空时填充。年限等规则一旦误判，AI 无法覆盖。第一轮应先提升规则正确性；后续可增加“低置信规则允许 AI 覆盖”的机制。

### 9.3 `.doc` 支持风险

`.doc` 需要额外依赖转换工具，Windows 本地环境可能不稳定。第一轮不做 `.doc` 解析，避免扩大安装和部署风险。

## 10. 建议提交拆分

建议分 3 个提交：

```text
Add resume parse and match diagnostic script
Improve resume parser rules for real samples
Improve fallback candidate matching dimensions
```

如果希望降低回滚成本，也可以先只提交诊断脚本和年限修复，再继续段落和匹配优化。
