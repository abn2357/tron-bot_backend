## Context

全新项目，从零搭建 tron-bot 后端。基于 architecture.mmd 架构设计，实现完整的 RAG 聊天链路。前端由 GitHub Pages 托管（独立仓库），本仓库只负责后端。Chroma 向量库文件假设已预先构建好，后端只做查询。

技术栈：Python + FastAPI，Redis 做状态存储，Claude API（Sonnet + Opus）做 LLM 调用，sentence-transformers 加载本地 bge-base-zh-v1.5 模型。

## Goals / Non-Goals

**Goals:**
- 实现从用户提问到流式回答的完整 RAG 链路
- IP 级限频 + 指纹级配额双重防刷
- 多轮对话支持（基于 SessionID 加载历史上下文）
- 配置化管理（配额、上下文窗口、模型参数等集中在配置文件）
- SSE 流式响应，降低用户感知延迟

**Non-Goals:**
- 向量库构建/更新 pipeline（假设已就绪）
- 用户认证/登录系统（仅用指纹 + SessionID）
- 前端实现
- 多机部署 / 负载均衡
- 管理后台

## Decisions

### 1. 项目结构

```
tron-bot_backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理（从 config.yaml 加载）
│   ├── routers/
│   │   └── chat.py          # /api/chat SSE 端点
│   ├── middleware/
│   │   └── rate_limit.py    # IP 限频中间件
│   ├── services/
│   │   ├── session.py       # 会话检查、配额校验、上下文加载
│   │   ├── rewriter.py      # 问题重写（Claude Sonnet）
│   │   ├── embedding.py     # 本地 Embedding（bge-base-zh-v1.5）
│   │   ├── retriever.py     # Chroma 向量检索
│   │   └── generator.py     # 最终生成（Claude Opus）+ SSE 流
│   └── models/
│       └── schemas.py       # Pydantic 请求/响应模型
├── config.yaml              # 运行时配置
├── requirements.txt
└── README.md
```

**理由**：按职责分层，每个 service 对应架构图中的一个处理节点，清晰映射。

### 2. 配置方案

使用 `config.yaml` + Pydantic Settings，支持环境变量覆盖。

```yaml
# 配额
quota:
  ip_rate_limit: 30          # 每个 IP 每分钟最多请求数
  user_daily_limit: 50       # 每个用户指纹每天最多请求数
  user_session_limit: 20     # 每个 Session 最多对话轮数

# 上下文
context:
  max_history_turns: 10      # 加载最近 N 轮对话作为上下文
  max_context_tokens: 4000   # 上下文最大 token 数（粗估）

# 模型
models:
  rewriter: "claude-sonnet-4-20250514"
  generator: "claude-opus-4-20250514"
  embedding: "BAAI/bge-base-zh-v1.5"

# 检索
retrieval:
  top_k: 5                   # 返回最相似的 K 个片段
  score_threshold: 0.5       # 最低相似度阈值

# Redis
redis:
  url: "redis://localhost:6379/0"
  history_ttl: 86400         # 对话历史 TTL：24 小时
  quota_ttl: 86400           # 配额计数 TTL：24 小时

# 服务
server:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["*"]        # 生产环境应限制为 GitHub Pages 域名
```

**理由**：
- `ip_rate_limit: 30/min`：防止脚本暴力刷接口，正常用户不会触发
- `user_daily_limit: 50`：单用户每天 50 次足够日常使用，控制 API 成本
- `max_history_turns: 10`：保留足够上下文又不至于太长
- `max_context_tokens: 4000`：给检索片段和历史对话留足空间，不挤占生成预算
- `top_k: 5`：检索 5 个片段，在召回率和精度之间平衡

### 3. API 设计

单一端点，POST + SSE：

```
POST /api/chat
Content-Type: application/json

{
  "question": "什么是...",
  "fingerprint": "abc123",
  "session_id": "sess_xyz"
}

Response: text/event-stream
data: {"token": "这"}
data: {"token": "是"}
...
data: {"done": true}
```

**理由**：简单直接，一个端点满足所有需求。POST 携带身份信息，SSE 流式返回。

### 4. Redis 数据结构

```
# 配额计数
quota:ip:{ip}             → Counter（TTL: 60s，滑动窗口）
quota:user:{fingerprint}  → Counter（TTL: 86400s，每日重置）

# 对话历史
history:{session_id}      → List of JSON strings（每项为 {role, content}）
                            TTL: 86400s
```

### 5. Embedding 模型加载

应用启动时加载一次 bge-base-zh-v1.5 到内存，后续请求复用。使用 FastAPI 的 lifespan 事件管理。

**理由**：模型 ~400MB，加载一次约 2-3 秒，不应每次请求重新加载。

### 6. Claude API 调用

使用 Anthropic Python SDK，Sonnet 做问题重写（非流式，等完整结果），Opus 做最终生成（流式，逐 token 返回）。

**理由**：重写需要完整结果才能做 embedding，必须等待；生成则应尽早返回，降低用户等待感。

## Risks / Trade-offs

- **Embedding 模型占内存 ~400MB** → 单机部署可接受；如果内存紧张，可考虑换 bge-small-zh-v1.5（~100MB，效果稍差）
- **IP 限频可被代理绕过** → 作为兜底手段够用，核心防线是指纹配额
- **指纹可伪造** → 已知风险，当前阶段可接受，后续可加验证码
- **Redis 单点** → 单机部署场景下可接受，挂了则配额失效但不影响核心问答（可降级跳过配额检查）
- **Sonnet 重写增加延迟** → 约 1-2s，换来更好的检索质量，值得
