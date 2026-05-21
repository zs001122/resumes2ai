# Frontend

Next.js 前端应用，负责 HR 工作台页面、简历上传、解析结果修正、候选人列表和详情。

当前前端已收缩为 V2 交付形态：围绕工作台、岗位、上传队列、候选人复核、人才库、重复复核和推荐摘要 Markdown，不再扩展新入口或新导出形态。

## 本地启动

```powershell
cd frontend
Copy-Item .env.example .env.local
npm run dev
```

如果是首次安装依赖：

```powershell
npm install
```

默认访问：

```text
http://localhost:3000
```

## 验收

```powershell
npm run lint
npm run build
```
