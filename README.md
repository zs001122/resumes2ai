# AI 简历筛选工作台

面向 HR 的 AI 简历筛选工作台。项目当前处于 V2 稳定化和简历解析质量增强实验阶段：主业务链路已冻结，不再直接往 V2 增加新业务功能；允许继续修复阻断验收、启动、解析质量和证据复核体验的问题。

## 当前状态

已形成可试用招聘初筛闭环：

```text
工作台总览
  -> 创建 / 管理岗位
  -> 上传简历
  -> 解析简历并生成候选人
  -> 自动评分与分项解释
  -> 候选人列表筛选与批量操作
  -> 候选人详情复核、备注、时间线
  -> 人才库沉淀与跨岗位搜索
  -> 岗位标准版本、历史重评、重复候选人人工复核
  -> 推荐摘要 Markdown 生成、编辑、复制、下载
```

当前实验分支重点是简历解析 vNext：不改 V2 主业务入口，通过 parse run、blocks、field candidates、source text 和人工修正页证据闭环，提高结构化字段质量。

## 技术栈

- 前端：Next.js + TypeScript + Tailwind CSS
- 后端：FastAPI + Python + SQLAlchemy
- 数据库：SQLite
- 文件存储：本地 `backend/uploads`

## 项目结构

```text
resumes2ai/
  backend/          FastAPI 后端、迁移、测试
  frontend/         Next.js 前端
  docs/             路线、记录、待办和模块文档
  scripts/api_tests 手动 API 验收脚本
```

## 本地启动

推荐一键启动前后端：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-dev.ps1
```

该脚本会补齐本地环境文件、执行后端迁移、启动后端 `8010` 和前端 `3000`，按 `Ctrl+C` 可同时停止两个服务。

也可以分别启动：

后端：

```powershell
cd backend
Copy-Item .env.example .env
.\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload --port 8010
```

如需启用 AI 简历结构化增强，在 `backend/.env` 中设置：

```text
AI_RESUME_PARSE_ENABLED=true
```

前端：

```powershell
cd frontend
Copy-Item .env.example .env.local
npm run dev
```

默认访问：

- 前端：http://localhost:3000
- 后端：http://localhost:8010
- 健康检查：http://localhost:8010/api/health

## 验收命令

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests

cd ..\frontend
npm run lint
npm run build
```

API 手动验收：

```powershell
python scripts/api_tests/06_v2_acceptance.py
```

真实样本解析与匹配诊断：

```powershell
cd backend
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

## 文档入口

核心文档：

- [ROADMAP.md](docs/ROADMAP.md)：长期主体开发路线，记录产品方向、版本路线、模块划分和冻结规则。
- [CHANGELOG.md](docs/CHANGELOG.md)：开发记录，按时间追加每轮背景、变更、验收、遗留问题和下一步。
- [BACKLOG.md](docs/BACKLOG.md)：待开发功能池，新业务能力先进入这里评估。

模块文档：

- [frontend.md](docs/modules/frontend.md)：前端 UI、页面、交互、修正页、证据展示。
- [backend.md](docs/modules/backend.md)：API、数据模型、上传链路、候选人、岗位、时间线。
- [parser.md](docs/modules/parser.md)：简历解析、vNext、section、field candidates、source text。
- [matching.md](docs/modules/matching.md)：匹配评分、解释、推荐摘要。
- [testing.md](docs/modules/testing.md)：验收脚本、fixtures、真实样本回归、测试策略。
- [operations.md](docs/modules/operations.md)：启动、环境、部署、本地数据、GitHub 凭据。

局部说明：

- [backend/README.md](backend/README.md)：后端启动、环境变量和验收。
- [frontend/README.md](frontend/README.md)：前端启动和验收。
- [scripts/api_tests/README.md](scripts/api_tests/README.md)：API 验收脚本说明。
