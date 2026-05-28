# AI 简历筛选工作台

面向 HR 的 AI 简历筛选工作台。当前项目已从 MVP 扩展到 V2.1.2，并完成整体收缩：V2 不再新增业务能力，只保留可试用招聘工作台的交付闭环、缺陷修复、验收脚本和启动说明。

## 当前边界

V2 交付范围：

- 工作台总览、待办和异常概览。
- 岗位创建、复制、暂停、重新开放、关闭和 JD 质量检查。
- 岗位内上传和统一上传。
- 简历解析、上传队列、失败重试和自动评分。
- 简历结构化抽取采用规则优先、AI 兜底增强：规则负责手机号、邮箱、明确键值对、日期区间、学校/公司归一化；AI 负责职责总结、技能熟练度、无结构项目描述和中英文混合文本。
- 候选人列表筛选、批量状态、批量入库和批量重评。
- 候选人详情、匹配解释、原文复核、备注和时间线。
- 轻量人才库、标签、历史岗位和跨岗位搜索。
- 岗位标准版本、历史候选人重评和评分追溯。
- 重复候选人人工复核。
- 推荐摘要 Markdown 生成、编辑、复制和下载。

V2 不再进入：

- 报告历史保存。
- 文本粘贴录入简历。
- ZIP 批量上传。
- PDF / Word 推荐报告导出。
- 后台异步任务队列。
- 自动合并重复候选人、候选人主档案合并、多岗位归属。
- 复杂权限、审批、面试日程、通知、ATS、Offer、招聘大屏和图片 OCR。

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
  docs/             设计、验收、交付和历史拆解文档
  scripts/api_tests 手动 API 验收脚本
```

## 本地启动

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

- [V2_STATUS_AND_ROADMAP.md](docs/V2_STATUS_AND_ROADMAP.md)：V2 当前状态、收缩边界和下一大版本候选池。
- [V2_RELEASE_CHECKLIST.md](docs/V2_RELEASE_CHECKLIST.md)：V2 稳定化、验收、演示和交付检查表。
- [RESUME_PARSE_MATCH_OPTIMIZATION_PLAN.md](docs/RESUME_PARSE_MATCH_OPTIMIZATION_PLAN.md)：基于真实简历样本的结构化提取与匹配优化实施方案。
- [V2_ACCEPTANCE_GUIDE.md](docs/V2_ACCEPTANCE_GUIDE.md)：V2 自动验收和手动回归路径。
- [HR_RESUME_SCREENING_TOOL_V2_DESIGN.md](docs/HR_RESUME_SCREENING_TOOL_V2_DESIGN.md)：V2 产品设计和模块边界。

历史拆解文档保留用于追溯，不再作为当前计划入口。
