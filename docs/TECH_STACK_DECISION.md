# AI 简历筛选工作台技术栈决策

## 1. 文档定位

本文档记录 MVP 阶段的技术栈选择和关键工程约束。

上位文档：

- [HR_RESUME_SCREENING_TOOL_DESIGN.md](./HR_RESUME_SCREENING_TOOL_DESIGN.md)
- [HR_RESUME_SCREENING_TOOL_MVP_DESIGN.md](./HR_RESUME_SCREENING_TOOL_MVP_DESIGN.md)
- [MVP_TASK_BREAKDOWN.md](./MVP_TASK_BREAKDOWN.md)

本技术栈用于实现 MVP，不改变整体产品设计方向。后续如需要替换数据库、文件存储或 AI 模型接口，应优先通过适配层替换，不应破坏业务模块边界。

## 2. 技术栈确认结果

### 2.1 架构

采用更工程化的前后端分离架构：

```text
Next.js 前端
  ↓ HTTP API
FastAPI 后端
  ↓
SQLite / 本地 uploads / 国内大模型 API
```

选择原因：

- 前端和后端职责清晰。
- FastAPI 更适合处理文件解析、AI 调用和后续异步任务。
- 后续如果需要扩展队列、OCR、对象存储或多模型适配，后端更容易演进。
- Next.js 专注 B 端工作台交互和页面体验。

## 3. 前端技术栈

### 3.1 核心框架

- Next.js
- TypeScript
- React

### 3.2 UI 与样式

- Tailwind CSS
- shadcn/ui
- lucide-react

### 3.3 表单与校验

- React Hook Form
- Zod

### 3.4 表格与列表

- TanStack Table

### 3.5 数据请求

- MVP 可使用 fetch 封装 API Client。
- 如交互复杂度提升，可引入 TanStack Query。

### 3.6 前端职责

- 岗位列表、创建、详情页面。
- 简历上传页面。
- 解析结果修正页面。
- 候选人列表和详情页面。
- 原简历预览和结构化字段并排展示。
- 调用后端 API，不直接访问数据库和文件系统。

## 4. 后端技术栈

### 4.1 核心框架

- FastAPI
- Python
- Pydantic
- Uvicorn

### 4.2 数据访问

MVP 使用 SQLite，后续需要替换为 PostgreSQL。

建议使用 SQLAlchemy 作为 ORM，Alembic 管理数据库迁移。

选择原因：

- SQLite 本地开发简单，不依赖额外数据库服务。
- SQLAlchemy 可以降低后续迁移 PostgreSQL 的成本。
- Alembic 可以保留可追踪的数据库结构变更。

### 4.3 后端职责

- 提供 REST API。
- 管理岗位、候选人、简历文件、匹配结果和状态流转。
- 处理文件上传和本地存储。
- 抽取 PDF、Word、TXT 文本。
- 调用国内大模型 API 和 OpenAI 兼容接口。
- 保存 AI 输出和人工修正记录。
- 为前端提供原简历预览和字段来源数据。

## 5. 数据库决策

### 5.1 MVP 数据库

MVP 使用 SQLite。

建议数据库文件：

```text
backend/data/resumes2ai.db
```

### 5.2 后续替换目标

后续替换为 PostgreSQL。

### 5.3 设计约束

- 不在业务代码中写死 SQLite 专属 SQL。
- 所有数据访问通过 ORM 或 Repository 层完成。
- JSON 字段在 SQLite 中可先用 TEXT 存储，业务层统一序列化和反序列化。
- 表结构命名应兼容 PostgreSQL。
- 主键、时间字段、状态字段从一开始保持规范，避免迁移时重构。

## 6. AI 模型接口决策

### 6.1 MVP 模型来源

支持两类模型接口：

- 国内大模型 API。
- 兼容 OpenAI 协议的自定义接口。

### 6.2 设计方式

后端必须封装统一 AI Provider 层。

建议接口形态：

```text
AIProvider
  - chat_json(messages, schema_hint)
  - parse_jd(jd_text)
  - parse_resume(resume_text)
  - match_candidate(job, candidate)
```

### 6.3 配置项

建议使用环境变量：

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_TIMEOUT_SECONDS=60
```

### 6.4 设计约束

- 业务代码不直接调用具体模型 SDK。
- 所有 AI 输出必须通过 JSON 解析和结构校验。
- AI 失败时必须记录错误原因。
- AI 任务需要支持重试入口。
- Prompt 和模型调用参数集中管理。
- 不允许基于敏感个人属性做推荐或淘汰。

## 7. 文件存储决策

### 7.1 MVP 存储方式

MVP 使用本地 uploads 目录。

建议目录：

```text
backend/uploads/
```

建议文件组织：

```text
backend/uploads/
  resumes/
    {resume_file_id}/
      original.pdf
      preview.txt
```

### 7.2 后续替换目标

后续替换为对象存储，例如：

- 阿里云 OSS
- MinIO
- S3 兼容存储

### 7.3 设计约束

- 业务代码不直接拼接本地文件路径。
- 后端封装 StorageService。
- 数据库只保存文件标识、相对路径或对象 key。
- 前端通过后端预览接口访问文件，不直接访问本地文件系统。
- 原始简历文件必须保留，不被人工修正内容覆盖。

## 8. 文件解析决策

### 8.1 MVP 支持格式

- PDF
- Word
- TXT

### 8.2 暂不支持

- 图片简历 OCR
- ZIP 批量包解析

### 8.3 建议解析库

- PDF：pypdf 或 pdfplumber
- Word：python-docx
- TXT：Python 原生读取

### 8.4 设计约束

- 文件解析封装为 ResumeParserService。
- 不同格式使用不同 parser，但输出统一结构。
- 抽取失败必须记录 parse_error。
- 预览失败时可以使用 parsed_text 作为兜底。
- P0 重点是文本抽取和原文件预览，P1 再做精确字段定位和高亮。

## 9. 后续可扩展能力

### 9.1 异步任务

MVP 可先同步处理上传后的解析和评分。

后续如文件较大或 AI 调用耗时明显，再引入：

- Celery
- Redis
- RQ

### 9.2 数据库升级

SQLite 到 PostgreSQL 的迁移路径：

1. 保持 SQLAlchemy 模型兼容。
2. 使用 Alembic 管理迁移脚本。
3. 将 JSON TEXT 字段调整为 PostgreSQL JSONB。
4. 替换数据库连接配置。
5. 执行数据迁移脚本。

### 9.3 文件存储升级

本地 uploads 到对象存储的迁移路径：

1. 保持 StorageService 接口不变。
2. 新增 OSS 或 S3 Storage 实现。
3. 将本地文件迁移到对象存储。
4. 更新数据库中的文件 key。
5. 前端仍通过后端预览接口访问。

### 9.4 AI Provider 升级

模型接口替换路径：

1. 保持 AIProvider 统一接口不变。
2. 新增新的 Provider 实现。
3. 使用环境变量切换模型。
4. 对关键任务执行 JSON 输出回归测试。

## 10. 推荐项目结构

```text
resumes2ai/
  frontend/
    app/
    components/
    lib/
    types/
    package.json

  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
        ai/
        storage/
        parsers/
      repositories/
    data/
    uploads/
    alembic/
    pyproject.toml

  docs/
```

## 10.1 当前落地状态

已创建 MVP 项目骨架：

- `frontend/`：Next.js + TypeScript + Tailwind CSS 基础结构。
- `backend/`：FastAPI 应用结构、健康检查接口、配置模块、SQLite 连接基础、AI/Parser/Storage 服务目录。
- `backend/data/`：SQLite 数据文件目录占位。
- `backend/uploads/`：本地文件存储目录占位。
- `backend/venv/`：后端 Python 虚拟环境，已安装 MVP 后端依赖。

已验证：

- 后端 Python 源码通过 `py_compile`。
- FastAPI 健康检查在临时 `8010` 端口验证通过。
- 前端依赖安装完成。
- Next.js 生产构建通过。
- Next.js 临时 dev server 首页访问通过。
- Git 仓库已初始化，远端已配置为 `https://github.com/zs001122/resumes2ai.git`。
- 首次项目骨架提交已推送到 GitHub `origin/main`，提交号 `61841dd`。

尚未完成：

- 创建数据库表和 Alembic 迁移。
- 实现业务接口。

## 11. 技术栈最终确认

MVP 阶段最终采用：

```text
前端：Next.js + TypeScript + Tailwind CSS + shadcn/ui
后端：FastAPI + Python + Pydantic
数据库：SQLite，后续替换 PostgreSQL
ORM：SQLAlchemy
迁移：Alembic
AI：国内大模型 API + OpenAI 兼容自定义接口
文件存储：本地 uploads，后续替换对象存储
文件解析：pypdf/pdfplumber + python-docx + TXT 原生读取
```
