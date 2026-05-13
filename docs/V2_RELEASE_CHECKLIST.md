# V2 稳定化与交付检查表

## 1. 文档定位

本文档用于 V2 功能冻结后的交付收口。V2.1.2 是 V2 功能截止版本；本文只记录稳定化、验收、演示和已知限制，不新增业务范围。

相关文档：

- [V2_STATUS_AND_ROADMAP.md](./V2_STATUS_AND_ROADMAP.md)：V2 完成范围、冻结边界和下一大版本候选池。
- [V2_ACCEPTANCE_GUIDE.md](./V2_ACCEPTANCE_GUIDE.md)：V2 自动验收和手动验收路径。

## 2. 自动验收状态

最近一次本地验证日期：2026-05-13。

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests

cd ..\frontend
npm run lint
npm run build
```

当前结果：

- 后端 pytest：通过，`4 passed`。
- 后端 ruff：通过。
- 前端 lint：通过。
- 前端生产构建：通过。
- Alembic 当前版本：`20260512_0009 (head)`。

## 3. 本地启动闭环

后端：

```powershell
cd backend
Copy-Item .env.example .env
.\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload --port 8010
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
- 后端健康检查：http://localhost:8010/api/health

## 4. 演示数据与环境重置

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

## 5. 手动验收闭环

按 [V2_ACCEPTANCE_GUIDE.md](./V2_ACCEPTANCE_GUIDE.md) 执行，重点覆盖：

- 工作台总览、今日待办、异常概览。
- 岗位创建、复制、暂停、重新开放、关闭。
- 开放和暂停岗位编辑，关闭岗位禁止编辑。
- 岗位标准版本历史和批量重新评分。
- 岗位内上传和统一上传。
- 上传队列、失败重试、重复风险统计。
- 候选人列表筛选、批量状态、批量入库、批量重评。
- 候选人详情、分项解释、原文高亮、备注、时间线。
- 轻量人才库、标签、历史岗位、跨岗位搜索。
- 重复候选人人工复核。
- 推荐摘要 Markdown 生成、编辑、复制、下载。

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

## 8. 交付结论

V2 当前可以作为“可试用招聘工作台”进入稳定化交付。下一步应围绕验收、演示和缺陷修复收口；报告历史、文本粘贴、ZIP、PDF / Word 导出等新能力进入下一大版本统一规划。
