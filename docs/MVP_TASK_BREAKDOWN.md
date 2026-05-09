# AI 简历筛选工作台 MVP 开发任务拆解

## 1. 文档定位

本文档用于将 MVP 设计拆解为可开发、可验收的工程任务清单。

上位文档：

- [HR_RESUME_SCREENING_TOOL_DESIGN.md](./HR_RESUME_SCREENING_TOOL_DESIGN.md)
- [HR_RESUME_SCREENING_TOOL_MVP_DESIGN.md](./HR_RESUME_SCREENING_TOOL_MVP_DESIGN.md)
- [TECH_STACK_DECISION.md](./TECH_STACK_DECISION.md)

执行原则：

- 严格遵循整体方案中的岗位驱动流程。
- MVP 只实现第一版初筛闭环，不扩展完整人才库、协作、大屏和外部系统集成。
- 如开发过程中需要改变整体设计方向、核心流程或 MVP 边界，必须先确认是否同步修改设计文档。

## 2. MVP 开发目标

第一版需要完成以下闭环：

```text
创建岗位
  ↓
AI 解析 JD
  ↓
确认岗位筛选标准
  ↓
上传简历
  ↓
解析简历
  ↓
原简历对照修正解析结果
  ↓
AI 匹配评分
  ↓
候选人列表筛选排序
  ↓
候选人详情复核
  ↓
状态流转
```

## 3. 开发阶段拆分

### 3.1 Phase 0：项目基础

#### 目标

搭建可以承载 MVP 的基础项目结构、开发环境和基础 UI 框架。

#### 状态

已完成。当前已创建 `frontend/` Next.js 骨架、`backend/` FastAPI 骨架、SQLite 数据目录、本地 uploads 目录、健康检查接口、基础配置和项目 README。后端已按要求使用 `backend/venv` 创建虚拟环境并安装依赖，前端依赖已安装。后端 Python 源码已通过 `py_compile` 语法检查，FastAPI 健康检查已在 `8010` 端口验证通过，Next.js 构建和临时 dev server 访问已验证通过。

#### 任务

- 初始化前端项目结构。
- 初始化后端项目结构。
- 配置数据库连接。
- 配置文件上传目录或对象存储抽象。
- 配置环境变量。
- 配置基础路由。
- 配置基础错误处理。
- 配置基础日志。
- 配置统一 API 响应格式。

#### 验收

- [x] 本地可以启动前端服务。
- [x] 本地可以启动后端服务。
- [x] 后端健康检查请求验证通过。
- [x] 数据库目录已创建。
- [x] 文件上传目录已创建。

### 3.2 Phase 1：岗位管理闭环

#### 目标

HR 可以创建岗位，填写 JD，并确认 AI 解析后的筛选标准。

#### 状态

已完成。当前已实现 `jobs` 数据库模型、Alembic 首个迁移、岗位 Repository、岗位 Pydantic Schema、本地 JD 解析占位服务和岗位管理 API。接口已通过临时 FastAPI 服务验证：`POST /api/jobs`、`GET /api/jobs`、`GET /api/jobs/{job_id}`、`POST /api/jobs/{job_id}/close`、`POST /api/jobs/parse-jd`。前端已完成岗位列表页、创建岗位页、岗位详情页的真实接口接入，支持 JD 解析、岗位保存、岗位详情查看和关闭岗位。后端源码已通过 `compileall` 和 `ruff check`，Alembic 当前版本为 `20260509_0001 (head)`，前端 `npm run build` 已通过。

#### 任务

- 实现岗位列表页。
- 实现创建岗位页。
- 实现岗位详情页。
- 实现岗位创建接口。
- 实现岗位更新接口。
- 实现岗位列表接口。
- 实现岗位详情接口。
- 实现 JD 解析接口。
- 实现岗位筛选标准编辑和保存。

#### 验收

- [x] 后端可以创建岗位。
- [x] 后端可以接收 JD。
- [x] 后端可以生成职责、必备条件、加分条件、排除条件和评分维度。
- [x] 后端可以保存 HR 最终确认后的岗位标准。
- [x] 后端可以查询岗位详情并展示最终筛选标准。
- [x] 前端岗位列表页接入真实接口。
- [x] 前端创建岗位页接入 JD 解析和保存接口。
- [x] 前端岗位详情页展示最终筛选标准。

### 3.3 Phase 2：简历上传与解析

#### 目标

HR 可以上传简历，系统完成文件保存、文本抽取和结构化解析。

#### 任务

- 实现简历上传页。
- 实现文件上传接口。
- 实现文件类型校验。
- 实现上传状态记录。
- 实现 PDF 文本抽取。
- 实现 Word 文本抽取。
- 实现 TXT 文本读取。
- 实现简历解析 AI 任务。
- 保存简历结构化结果。
- 保存简历原始文件地址。
- 保存解析原文文本。
- 保存低置信度字段。
- 保存字段来源信息。

#### 验收

- HR 可以上传 PDF、Word、TXT 文件。
- 不支持的文件类型会被拦截并提示。
- 上传成功后可以看到解析状态。
- 解析失败会记录失败原因。
- 解析成功后可以生成候选人基础信息、工作经历、项目经历和技能。

### 3.4 Phase 3：原简历对照修正

#### 目标

HR 可以在原简历预览旁修正结构化解析结果。

#### 任务

- 实现解析结果修正页。
- 实现原简历预览组件。
- 实现结构化字段编辑表单。
- 实现字段保存接口。
- 实现人工修改记录保存。
- 实现低置信度字段标记。
- 实现修正后触发重新匹配评分的入口或流程。
- 预留字段定位和高亮的数据结构。

#### P0 范围

- 左侧展示结构化字段。
- 右侧展示原简历预览。
- HR 可以编辑并保存字段。
- 系统记录修改前后的值。

#### P1 范围

- 点击字段定位到原文位置。
- 原文片段高亮。
- 关键词命中展示。

#### 验收

- 结构化字段和原简历可以并排查看。
- HR 修改字段后可以保存。
- 修改记录可以查询。
- 原始简历文件不会被覆盖。
- 修正后的字段会参与后续匹配评分。

### 3.5 Phase 4：AI 匹配评分

#### 目标

系统可以基于岗位标准和候选人解析结果生成匹配分、推荐等级和解释。

#### 任务

- 实现匹配评分接口。
- 实现匹配评分 AI 任务。
- 保存匹配结果。
- 支持解析完成后自动评分。
- 支持人工修正后重新评分。
- 支持评分失败重试。
- 在候选人列表展示评分结果。
- 在候选人详情展示评分解释。

#### 验收

- 每个候选人都有总匹配分。
- 每个候选人都有推荐等级。
- 每个候选人都有匹配理由。
- 每个候选人可以展示短板和风险点。
- 风险点以“待确认”方式呈现。
- 人工修正字段后可以重新生成匹配结果。

### 3.6 Phase 5：候选人列表与详情

#### 目标

HR 可以按岗位查看候选人，筛选、排序并进入详情复核。

#### 任务

- 实现候选人列表页。
- 实现候选人详情页。
- 实现候选人列表接口。
- 实现候选人详情接口。
- 实现候选人筛选。
- 实现候选人排序。
- 实现候选人状态更新。
- 实现候选人详情中的原简历预览。
- 实现候选人详情中的 AI 分析展示。
- 实现候选人详情中的编辑解析结果入口。

#### 验收

- 候选人可以按岗位查看。
- 候选人可以按匹配分排序。
- 候选人可以按推荐等级、状态、城市、年限筛选。
- HR 可以进入候选人详情。
- 详情页可以看到 AI 分析、结构化信息和原简历。
- HR 可以修改候选人状态。

### 3.7 Phase 6：MVP 收尾与验收

#### 目标

完成端到端联调、异常处理和 MVP 验收。

#### 任务

- 端到端跑通主流程。
- 补充空状态页面。
- 补充错误提示。
- 补充加载状态。
- 补充基础表单校验。
- 补充接口异常处理。
- 补充关键流程测试数据。
- 整理 MVP 使用说明。

#### 验收

- 可以从创建岗位跑到候选人状态流转。
- 常见异常有清晰提示。
- 上传失败、解析失败、AI 评分失败都有可恢复入口。
- MVP 验收清单全部通过。

## 4. 前端页面任务

### 4.1 岗位列表页

#### 路由建议

```text
/jobs
```

#### 页面内容

- 岗位列表表格
- 岗位状态标签
- 候选人数量
- 高匹配候选人数量
- 待筛选数量
- 创建岗位按钮

#### 操作

- 创建岗位
- 查看岗位详情
- 编辑岗位
- 关闭岗位

### 4.2 创建岗位页

#### 路由建议

```text
/jobs/new
```

#### 页面内容

- 岗位基础信息表单
- JD 文本输入框
- AI 解析按钮
- AI 解析结果编辑区

#### 操作

- 保存草稿
- 解析 JD
- 保存岗位

### 4.3 岗位详情页

#### 路由建议

```text
/jobs/:jobId
```

#### 页面内容

- 岗位基础信息
- 岗位筛选标准
- 候选人统计
- 简历上传入口
- 候选人列表入口

#### 操作

- 编辑岗位标准
- 上传简历
- 查看候选人

### 4.4 简历上传页

#### 路由建议

```text
/jobs/:jobId/resumes/upload
```

#### 页面内容

- 文件上传区域
- 支持格式说明
- 上传队列
- 解析状态
- 失败原因

#### 操作

- 选择文件
- 上传文件
- 重新上传
- 进入解析结果修正

### 4.5 解析结果修正页

#### 路由建议

```text
/jobs/:jobId/candidates/:candidateId/review
```

#### 页面内容

- 结构化字段编辑区
- 原简历预览区
- 低置信度字段标记
- 修改记录入口

#### 操作

- 编辑字段
- 保存字段
- 重新评分
- 返回候选人详情

### 4.6 候选人列表页

#### 路由建议

```text
/jobs/:jobId/candidates
```

#### 页面内容

- 筛选器
- 候选人表格
- 匹配分
- 推荐等级
- 风险标签
- 状态标签

#### 操作

- 筛选
- 排序
- 修改状态
- 进入详情

### 4.7 候选人详情页

#### 路由建议

```text
/jobs/:jobId/candidates/:candidateId
```

#### 页面内容

- AI 匹配分析
- 结构化简历信息
- 原简历预览
- 状态操作区

#### 操作

- 标记已收藏
- 标记待沟通
- 标记已淘汰
- 标记已入库
- 编辑解析结果
- 重新评分

## 5. 后端接口任务

### 5.1 岗位接口

```text
GET    /api/jobs
POST   /api/jobs
GET    /api/jobs/:jobId
PATCH  /api/jobs/:jobId
POST   /api/jobs/:jobId/close
POST   /api/jobs/parse-jd
```

#### 说明

- `POST /api/jobs/parse-jd` 接收 JD 文本，返回职责、必备条件、加分条件、排除条件和评分维度。
- `POST /api/jobs` 保存 HR 最终确认后的岗位标准。

### 5.2 简历文件接口

```text
POST   /api/jobs/:jobId/resumes/upload
GET    /api/resume-files/:resumeFileId
GET    /api/resume-files/:resumeFileId/preview
POST   /api/resume-files/:resumeFileId/parse
```

#### 说明

- 上传接口负责保存原始文件并创建解析任务。
- 预览接口返回可展示的 PDF、HTML 或文本内容。
- 解析接口可用于失败重试。

### 5.3 候选人接口

```text
GET    /api/jobs/:jobId/candidates
GET    /api/jobs/:jobId/candidates/:candidateId
PATCH  /api/candidates/:candidateId
PATCH  /api/jobs/:jobId/candidates/:candidateId/status
GET    /api/candidates/:candidateId/correction-logs
```

#### 说明

- 候选人列表接口支持筛选和排序参数。
- 候选人详情接口返回结构化信息、匹配结果、状态和简历文件。
- 候选人更新接口用于保存人工修正后的字段。

### 5.4 匹配评分接口

```text
POST   /api/jobs/:jobId/candidates/:candidateId/match
GET    /api/jobs/:jobId/candidates/:candidateId/match
```

#### 说明

- `POST` 用于生成或重新生成匹配评分。
- `GET` 用于读取最新匹配结果。

### 5.5 字段来源接口

```text
GET    /api/resume-files/:resumeFileId/field-extractions
```

#### 说明

- MVP P0 可以只返回字段名、解析值、置信度和原文片段。
- P1 再返回页码、文本位置或坐标，用于点击定位和高亮。

## 6. 数据表任务

### 6.1 jobs

| 字段 | 说明 |
|---|---|
| id | 岗位 ID |
| title | 岗位名称 |
| department | 部门 |
| location | 工作地点 |
| salary_range | 薪资范围 |
| experience_required | 年限要求 |
| education_required | 学历要求 |
| jd | JD 原文 |
| responsibilities | 岗位职责 |
| must_have | 必备条件 |
| nice_to_have | 加分条件 |
| deal_breakers | 排除条件 |
| scoring_dimensions | 评分维度 |
| status | open / closed |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### 6.2 resume_files

| 字段 | 说明 |
|---|---|
| id | 简历文件 ID |
| job_id | 岗位 ID |
| candidate_id | 候选人 ID |
| file_name | 文件名 |
| file_type | 文件类型 |
| file_url | 原始文件地址 |
| preview_url | 预览地址 |
| parsed_text | 抽取文本 |
| upload_status | 上传状态 |
| parse_status | 解析状态 |
| parse_error | 解析失败原因 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### 6.3 candidates

| 字段 | 说明 |
|---|---|
| id | 候选人 ID |
| name | 姓名 |
| phone | 手机号 |
| email | 邮箱 |
| city | 城市 |
| current_company | 当前公司 |
| current_title | 当前岗位 |
| years_of_experience | 工作年限 |
| highest_education | 最高学历 |
| skills | 技能 |
| education | 教育经历 |
| work_experiences | 工作经历 |
| project_experiences | 项目经历 |
| low_confidence_fields | 低置信度字段 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### 6.4 candidate_matches

| 字段 | 说明 |
|---|---|
| id | 匹配结果 ID |
| job_id | 岗位 ID |
| candidate_id | 候选人 ID |
| score | 总分 |
| level | 推荐等级 |
| summary | 一句话总结 |
| matched_points | 匹配点 |
| weak_points | 短板 |
| risks | 风险点 |
| interview_questions | 面试问题 |
| created_at | 创建时间 |

### 6.5 candidate_job_statuses

| 字段 | 说明 |
|---|---|
| id | 状态 ID |
| job_id | 岗位 ID |
| candidate_id | 候选人 ID |
| status | pending / favorite / pending_contact / rejected / archived |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### 6.6 field_correction_logs

| 字段 | 说明 |
|---|---|
| id | 修改记录 ID |
| candidate_id | 候选人 ID |
| resume_file_id | 简历文件 ID |
| field_name | 字段名 |
| old_value | 修改前 |
| new_value | 修改后 |
| editor_id | 修改人 |
| created_at | 创建时间 |

### 6.7 resume_field_extractions

| 字段 | 说明 |
|---|---|
| id | 字段来源 ID |
| resume_file_id | 简历文件 ID |
| candidate_id | 候选人 ID |
| field_name | 字段名 |
| extracted_value | 解析值 |
| confidence | 置信度 |
| source_text | 原文片段 |
| page_number | 页码 |
| text_start_offset | 文本起始位置 |
| text_end_offset | 文本结束位置 |
| bounding_box | 坐标信息 |
| created_at | 创建时间 |

## 7. AI 任务拆解

### 7.1 JD 解析任务

#### 输入

- 岗位名称
- JD 原文
- 年限要求
- 学历要求

#### 输出

- responsibilities
- must_have
- nice_to_have
- deal_breakers
- scoring_dimensions

#### 验收

- 输出为结构化 JSON。
- 必备条件和加分条件必须分开。
- 不确定的要求不得强行归为硬性排除条件。

### 7.2 简历解析任务

#### 输入

- 简历抽取文本
- 文件类型
- 岗位上下文，可选

#### 输出

- 候选人基础信息
- 教育经历
- 工作经历
- 项目经历
- 技能关键词
- 低置信度字段
- 字段来源信息

#### 验收

- 输出为结构化 JSON。
- 不得编造简历中不存在的信息。
- 对不确定字段标记低置信度。
- 字段来源应尽量包含原文片段。

### 7.3 匹配评分任务

#### 输入

- 岗位筛选标准
- 候选人结构化简历

#### 输出

- score
- level
- summary
- matched_points
- weak_points
- risks
- interview_questions

#### 验收

- 输出为结构化 JSON。
- 分数必须有解释。
- 风险点必须以“待确认”方式表达。
- 不得基于敏感个人属性做推荐或淘汰。

## 8. 文件解析任务

### 8.1 文件上传

#### 任务

- 限制文件类型。
- 限制文件大小。
- 保存原始文件。
- 生成文件记录。
- 返回上传状态。

#### 验收

- 支持 PDF、Word、TXT。
- 原始文件可下载或预览。
- 上传失败有明确提示。

### 8.2 文本抽取

#### 任务

- PDF 文本抽取。
- Word 文本抽取。
- TXT 文本读取。
- 抽取失败时记录原因。
- 保存 `parsed_text`。

#### 验收

- 文本型 PDF 可以抽取主要内容。
- Word 可以抽取主要内容。
- TXT 可以完整读取。
- 抽取结果可供 AI 解析使用。

### 8.3 文件预览

#### P0 任务

- PDF 使用原文件预览。
- Word 转换为可预览格式，或提供文本预览兜底。
- TXT 使用文本预览。

#### P1 任务

- 统一预览层。
- 支持字段定位。
- 支持原文高亮。

#### 验收

- HR 在修正页和详情页可以看到原简历内容。
- 预览失败时可以查看抽取文本作为兜底。

## 9. MVP 总体验收清单

### 9.1 主流程验收

- 可以创建岗位。
- 可以解析 JD。
- 可以确认岗位筛选标准。
- 可以上传简历。
- 可以解析简历。
- 可以对照原简历修正解析结果。
- 可以生成匹配评分。
- 可以查看候选人列表。
- 可以筛选和排序候选人。
- 可以查看候选人详情。
- 可以修改候选人状态。

### 9.2 数据验收

- 岗位数据保存正确。
- 简历原始文件保存正确。
- 简历抽取文本保存正确。
- 候选人结构化信息保存正确。
- 字段修改记录保存正确。
- 匹配结果保存正确。
- 候选人状态保存正确。

### 9.3 AI 验收

- JD 解析结果结构稳定。
- 简历解析结果结构稳定。
- 匹配评分结果结构稳定。
- AI 输出不包含额外非 JSON 文本。
- AI 不基于敏感属性做判断。
- AI 对不确定内容标记待确认。

### 9.4 异常验收

- 文件类型不支持时有提示。
- 文件上传失败时有提示。
- 文本抽取失败时有提示。
- AI 解析失败时有重试入口。
- AI 评分失败时有重试入口。
- 空列表有空状态。
- 接口失败有错误提示。

### 9.5 边界验收

- MVP 不实现完整人才库页面。
- MVP 不实现多人协作。
- MVP 不实现招聘数据大屏。
- MVP 不实现外部招聘平台导入。
- MVP 不实现面试日程管理。
- MVP 保留后续扩展字段和状态。

## 10. 推荐开发顺序

1. 项目基础和数据库结构。
2. 岗位管理与 JD 解析。
3. 简历上传与文本抽取。
4. 简历结构化解析。
5. 原简历对照修正。
6. AI 匹配评分。
7. 候选人列表。
8. 候选人详情。
9. 状态流转。
10. 端到端验收和异常处理。

## 11. 暂不实现清单

以下能力不进入 MVP 开发范围：

- 图片简历 OCR。
- ZIP 批量包解析。
- 完整人才库页面。
- 人才库智能推荐。
- 多 HR 协作。
- 面试官评价。
- 邮件或短信通知。
- 企业微信或飞书集成。
- 招聘渠道分析。
- Offer 流程。
- ATS 对接。

如后续需要提前实现上述能力，必须先确认是否调整 MVP 范围，并同步更新设计文档。
