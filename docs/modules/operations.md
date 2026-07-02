# 工程运维模块文档

## 模块定位

工程运维模块记录本地启动、端口、环境变量、数据库、上传文件、GitHub 凭据、分支和常见运行问题。

## 本地服务

推荐一键启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-dev.ps1
```

常用端口：

- 后端：`8010`
- 前端默认：`3000`
- 当前开发机前端常用：`3010`

后端健康检查：

```text
http://localhost:8010/api/health
```

## 环境变量

后端真实密钥放在 `backend/.env`，不要提交。

```text
AI_API_KEY=...
AI_RESUME_PARSE_ENABLED=true
```

AI 简历结构化增强默认关闭，需要时再启用。

## 数据和文件

- SQLite 本地数据库用于开发和验收。
- 上传文件存放在 `backend/uploads`。
- `test_data/` 用于本地真实脱敏样本，不提交原始简历。
- 清理演示数据优先使用 `scripts/api_tests/08_clear_all.py`，不要手工删库。

## Git 和 GitHub 凭据

当前实验分支：

```text
experiment/resume-parse-vnext
```

SSH 公钥通常放在本机：

```text
~/.ssh/id_ed25519.pub
```

GitHub 配置位置：

- GitHub 网页：Settings -> SSH and GPG keys -> New SSH key。
- 本机私钥保存在 `~/.ssh/`，不要提交到仓库。
- `known_hosts` 由首次连接或 `ssh-keyscan github.com` 维护。

常用检查：

```bash
git status --short --branch
git remote -v
ssh -T git@github.com
```

## 常见运行问题

### 前端 3010 端口监听但页面不返回

现象：

- `ss -ltnp` 显示 Next 进程占用 3010。
- `curl -I http://127.0.0.1:3010` 超时。

处理：

1. 找到占用 3010 的 `next-server` PID。
2. 先普通 `kill <pid>`。
3. 如果仍不释放端口，再 `kill -9 <pid>`。
4. 重新运行：

```bash
cd frontend
npm run dev -- --hostname 0.0.0.0 --port 3010
```

### Next 静态资源 404

现象：

- 浏览器报 `_next/static/... 404`。

处理：

- 清理 `frontend/.next` 后重启 dev server。
- 确认访问端口和当前 Next 进程端口一致。

## 维护规则

- 启动、端口、凭据、部署、运行状态问题记录在本文档。
- 代码开发记录写入 `CHANGELOG.md`。
- 模块技术方案写入对应 `modules/*.md`。
