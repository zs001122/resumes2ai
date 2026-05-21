# API 测试脚本

这些脚本用于手动测试 MVP 到 V2 的接口。当前交付入口以 V2 验收为准，优先运行 `06_v2_acceptance.py`；其他脚本保留用于局部排查。

运行前请先启动后端：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8010
```

默认 API 地址是：

```text
http://localhost:8010
```

如需修改：

```powershell
$env:RESUMES2AI_API_BASE_URL="http://localhost:8010"
```

## 脚本说明

```powershell
# 1. 健康检查
python scripts/api_tests/01_health.py

# 2. 岗位模块：解析 JD、创建岗位、查询列表和详情
python scripts/api_tests/02_jobs.py

# 3. 简历上传与解析，需要填入 02_jobs.py 输出的 JOB_ID
python scripts/api_tests/03_upload_resume.py --job-id <JOB_ID>

# 4. 候选人流程，需要填入 JOB_ID；candidate-id 可不传，默认取列表第一个
python scripts/api_tests/04_candidates.py --job-id <JOB_ID>

# 5. 完整端到端流程：创建岗位、上传简历、修正、评分、状态流转
python scripts/api_tests/05_e2e.py

# 6. V2 验收流程：工作台、岗位、上传队列、重试评分、组合筛选、批量操作、解释、时间线、人才库、标准版本、重复复核和推荐摘要
python scripts/api_tests/06_v2_acceptance.py

# 7. 删除指定岗位及该岗位下不再关联其他岗位的候选人。默认只预览，追加 --yes 执行删除
python scripts/api_tests/07_delete_job.py --job-id <JOB_ID>
python scripts/api_tests/07_delete_job.py --job-id <JOB_ID> --yes

# 8. 全量清空所有岗位、候选人、上传记录和 uploads 文件。默认只预览，追加 --yes 执行删除
python scripts/api_tests/08_clear_all.py
python scripts/api_tests/08_clear_all.py --yes
```

默认简历样例使用：

```text
简历数据/数据开发-杨晓飞.pdf
```

可通过 `--file` 指定其他 PDF、DOCX 或 TXT 文件。

## 收缩后的使用建议

- 日常交付验收：运行 `06_v2_acceptance.py`。
- 清理演示环境：先运行 `08_clear_all.py` 预览，再追加 `--yes`。
- 局部接口排查：按需运行 `01` 到 `05`。
- 删除单个演示岗位：运行 `07_delete_job.py`，默认预览，确认后追加 `--yes`。
