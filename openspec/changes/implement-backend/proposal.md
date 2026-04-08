## Why

需要实现 tron-bot 的后端服务，为前端（GitHub Pages）提供 RAG 聊天能力。用户通过浏览器提问，后端完成问题重写、向量检索、大模型生成并以 SSE 流式返回答案。向量库已准备就绪，现在需要搭建完整的后端请求链路。

## What Changes

- 新建 FastAPI 项目，包含完整的 RAG 请求处理链路
- 实现 IP 级限频，防止滥用
- 实现基于用户指纹 + SessionID 的配额校验与历史对话加载
- 集成 Claude API：Sonnet 用于问题重写，Opus 用于最终生成
- 集成本地 Embedding 模型（bge-base-zh-v1.5）进行向量化
- 集成 Chroma 向量库进行语义检索
- 实现 SSE 流式响应
- 使用 Redis 存储配额计数和对话历史
- 对话完成后将问答写回 Redis
- 提供配置文件管理配额限制、上下文窗口等参数

## Capabilities

### New Capabilities

- `api-gateway`: API 入口、IP 限频、CORS、SSE 流式响应
- `session-management`: 会话检查、配额校验、历史对话加载（Redis）
- `rag-pipeline`: 问题重写（Sonnet）→ Embedding（bge-base-zh-v1.5）→ 向量检索（Chroma）→ 生成（Opus）
- `app-config`: 集中配置管理（配额、上下文窗口、模型参数、Redis 连接等）

### Modified Capabilities

（无，全新项目）

## Impact

- **新增依赖**: FastAPI, uvicorn, redis, chromadb, sentence-transformers, anthropic SDK, sse-starlette
- **外部服务**: Redis（需本地或远程实例）、Claude API（需 API Key）
- **预置数据**: Chroma 向量库文件（假设已存在）
- **部署**: 单机运行，uvicorn 启动
