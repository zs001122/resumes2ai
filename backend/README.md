# Backend

FastAPI 后端服务，负责 API、SQLite 数据访问、文件上传、简历解析和 AI Provider 适配。

当前后端已收缩为 V2 交付形态，维护岗位、上传、解析、评分、候选人复核、人才库、重复复核和推荐摘要 Markdown 的闭环。

简历结构化解析采用规则优先、AI 兜底增强：

- 规则层：手机号、邮箱、明确键值对、日期区间工作年限、学校/公司归一化。
- AI 层：职责总结、技能熟练度、工作/项目自由文本、中英文混合文本。
- 默认关闭 AI 增强，设置 `AI_RESUME_PARSE_ENABLED=true` 后启用。

## 本地启动

```powershell
cd backend
Copy-Item .env.example .env
.\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload --port 8010
```

如果是首次安装依赖：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## 环境变量

真实密钥请放在 `backend/.env`，不要写入 `.env.example`。

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写：

```text
AI_API_KEY=你的真实 DeepSeek Key
```

健康检查：

```text
GET http://localhost:8010/health
GET http://localhost:8010/api/health
```

## 验收

```powershell
cd backend
.\venv\Scripts\Activate.ps1
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests
```
