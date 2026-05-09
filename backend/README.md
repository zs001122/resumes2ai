# Backend

FastAPI 后端服务，负责 API、SQLite 数据访问、文件上传、简历解析和 AI Provider 适配。

## 本地启动

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn app.main:app --reload --port 8010
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

## 数据库迁移

```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```
