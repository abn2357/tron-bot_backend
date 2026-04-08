## 1. 项目初始化

- [x] 1.1 创建项目目录结构（app/routers, app/middleware, app/services, app/models）
- [x] 1.2 创建 requirements.txt（fastapi, uvicorn, redis, chromadb, sentence-transformers, anthropic, sse-starlette, pyyaml）
- [x] 1.3 创建 config.yaml 配置文件（配额、上下文、模型、检索、Redis、服务器参数）
- [x] 1.4 实现 app/config.py 配置加载（YAML 读取 + 环境变量覆盖 + Pydantic 校验）

## 2. 核心框架

- [x] 2.1 实现 app/main.py FastAPI 应用入口（lifespan 事件加载 Embedding 模型、初始化 Redis 和 Chroma 连接）
- [x] 2.2 实现 app/models/schemas.py 请求/响应 Pydantic 模型
- [x] 2.3 实现 app/middleware/rate_limit.py IP 限频中间件（Redis 滑动窗口计数）

## 3. 会话管理

- [x] 3.1 实现 app/services/session.py 配额校验（用户指纹每日限额 + Session 轮数限制）
- [x] 3.2 实现 app/services/session.py 历史对话加载（从 Redis 读取最近 N 轮）
- [x] 3.3 实现 app/services/session.py 对话历史保存（问答写入 Redis + TTL）

## 4. RAG Pipeline

- [x] 4.1 实现 app/services/rewriter.py 问题重写（Claude Sonnet 调用，传入历史上下文）
- [x] 4.2 实现 app/services/embedding.py 文本向量化（bge-base-zh-v1.5 模型推理）
- [x] 4.3 实现 app/services/retriever.py 向量检索（Chroma 查询，top_k + score_threshold 过滤）
- [x] 4.4 实现 app/services/generator.py 流式生成（Claude Opus 调用，组装 system prompt + 检索片段 + 上下文）

## 5. API 端点

- [x] 5.1 实现 app/routers/chat.py POST /api/chat 端点（串联完整 RAG 链路，SSE 流式返回）
- [x] 5.2 添加 CORS 中间件配置
- [x] 5.3 添加错误处理（配额超限 429、参数错误 422、内部错误 500、生成中断 SSE error 事件）
