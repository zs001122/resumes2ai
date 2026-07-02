# 测试与验收模块文档

## 模块定位

测试模块负责自动化测试、手动 API 验收、真实样本回归、fixtures 和演示数据清理。

当前原则：

- V2 主流程必须可持续验收。
- parser 和 matching 改动必须有真实样本或 fixtures 回归。
- 不跑某类验证时，需要在开发记录中说明原因。

## 当前测试入口

后端：

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests scripts
```

前端：

```powershell
cd frontend
npm run lint
npm run build
```

API 验收：

```powershell
python scripts/api_tests/06_v2_acceptance.py
```

真实样本解析与匹配诊断：

```powershell
cd backend
.\venv\Scripts\python.exe scripts\diagnose_resume_parse_match.py --sample-dir ..\简历数据 --job-profile software-intern
```

## 真实样本和 fixtures

当前测试数据来源：

- `backend/tests/fixtures/resume_parser_vnext/`：脱敏 parser fixtures。
- `test_data/`：本地真实脱敏样本，已 git ignore，不提交原始简历。
- `简历数据/`：历史真实样本诊断目录，本地存在时可运行诊断脚本。

记录要求：

- 样本原文不提交。
- 可提交脱敏文本 fixtures 和 expected JSON。
- 每次 parser 改动记录关键字段、经历数量、低置信字段和 source text 变化。

## 验收清单

V2 主链路：

- 工作台可访问。
- 岗位创建、复制、暂停、重开、关闭可用。
- 上传队列和失败重试可用。
- 解析成功后生成候选人和评分。
- 候选人列表筛选和批量操作可用。
- 候选人详情、匹配解释、备注、时间线可用。
- 人才库和标签可用。
- 标准版本和批量重评可用。
- 重复候选人人工复核可用。

vNext parser：

- parse run 版本符合预期。
- blocks 覆盖 basics、education、work、projects、skills 等关键 section。
- field candidates 包含 extractor、confidence、source_text、rejection_reason。
- 低置信字段排序和修正页降级行为正常。

## 演示数据清理

预览：

```powershell
python scripts/api_tests/08_clear_all.py
```

确认清空：

```powershell
python scripts/api_tests/08_clear_all.py --yes
```

保留 uploads 文件：

```powershell
python scripts/api_tests/08_clear_all.py --yes --keep-files
```

## 维护规则

- 新增测试策略、样本回归、验收命令写在本文档。
- 具体 parser 缺陷写入 `parser.md`。
- 每轮开发验证结果追加到 `CHANGELOG.md`。
