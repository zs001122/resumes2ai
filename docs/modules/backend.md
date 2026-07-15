# 后端模块文档

## 模块定位

后端负责 API、数据模型、文件处理、简历解析、匹配评分、时间线、人才库和重复复核等核心业务能力。

当前原则：

- V2 主流程保持稳定。
- 不为 V2 增加新业务模型或新入口。
- 解析质量增强可以通过 parse run、blocks、field candidates 等证据表增强，但不破坏现有上传和候选人生成链路。

## 当前能力

### API 和业务对象

- 岗位创建、复制、暂停、重开、关闭。
- JD 质量检查和岗位漏斗统计。
- 岗位内上传和统一上传。
- 上传任务状态、失败原因、重试。
- 候选人列表、详情、状态、备注、时间线。
- 批量状态、批量入库、批量重评。
- 人才库、标签、跨岗位搜索。
- 岗位标准版本和历史候选人重评。
- 重复候选人识别和人工复核。
- 推荐摘要 Markdown 接口。

### 数据和追溯

- 候选人岗位状态与人才库状态分离。
- 操作时间线追加写入，不覆盖历史。
- 岗位上下文校验，避免跨岗位误操作。
- 匹配结果关联岗位标准版本。
- parse run、blocks、field candidates 支持 vNext evidence。

## 当前重点

- 保持上传后现有 API 主流程不变。
- 解析 vNext 只增强 parse run、blocks、field candidates 的质量。
- 修正日志继续记录 new_value；不新增数据库结构，已复用 `FieldCorrectionLog.editor_id` 记录 `local` 或 `vnext:<extractor>@<confidence>` 来源。
- 后续如要把人工修正反馈自动转成 parser training/eval data，需要先进入 backlog 或 parser 模块方案。

## 风险点

- 新数据模型会影响迁移、旧数据兼容和 V2 冻结边界。
- 上传处理异步化属于下一大版本候选，不直接回流 V2。
- 自动合并重复候选人会改变候选人主档案模型，不进入当前阶段。

## 验收

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests
.\venv\Scripts\python.exe -m ruff check app tests scripts
```

关键回归：

- 岗位上下文接口不能跨岗位操作候选人。
- 上传重试成功后继续执行解析、重复识别和评分。
- 标准版本变更后重评结果关联最新版本。
- 重复复核只记录人工判断，不自动合并候选人。
- vNext parse run 不存在时前端仍可走旧体验。

## 维护规则

- API、模型、迁移和 repository 调整记录在本文档。
- 解析算法细节记录在 `parser.md`。
- 匹配评分细节记录在 `matching.md`。
- 测试策略和样本回归记录在 `testing.md`。
