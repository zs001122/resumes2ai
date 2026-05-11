# API 测试脚本

这些脚本用于手动测试 MVP 各模块接口。运行前请先启动后端：

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

# 6. V2 验收流程：工作台、上传队列、组合筛选、批量操作、解释、时间线、人才库和岗位增强
python scripts/api_tests/06_v2_acceptance.py

# 7. 删除指定岗位及该岗位下不再关联其他岗位的候选人。默认只预览，追加 --yes 执行删除
python scripts/api_tests/07_delete_job.py --job-id <JOB_ID>
python scripts/api_tests/07_delete_job.py --job-id <JOB_ID> --yes
```

默认简历样例使用：

```text
简历数据/数据开发-杨晓飞.pdf
```

可通过 `--file` 指定其他 PDF、DOCX 或 TXT 文件。
