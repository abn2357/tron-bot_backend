# Tron Bot Backend

基于 RAG（检索增强生成）的中文知识问答机器人后端服务。

## 技术栈

- **框架**: FastAPI + SSE 流式响应
- **LLM**: Claude API（Sonnet 问题重写 + Opus 回答生成）
- **Embedding**: bge-base-zh-v1.5（本地模型）
- **向量库**: Chroma
- **存储**: Redis（配额计数 + 对话历史）

## 架构

```
用户提问 → IP限频 → 配额校验/上下文加载(Redis)
         → 问题重写(Sonnet) → Embedding(bge-base-zh)
         → 向量检索(Chroma) → 流式生成(Opus) → SSE返回
```

## 快速开始

### 前置条件

- Python 3.10+
- Redis 运行中
- Chroma 向量库已构建（`./chroma_db` 目录下需有 `knowledge_base` collection）
- Anthropic API Key

### 安装与运行

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Claude API 密钥 | 无（必填） |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `SERVER_PORT` | 服务端口 | `8000` |
| `CORS_ORIGINS` | 允许的跨域来源（逗号分隔） | `*` |

## API

### POST /api/chat

```json
{
  "question": "你的问题",
  "fingerprint": "用户指纹",
  "session_id": "会话ID"
}
```

响应：`text/event-stream`

```
data: {"token": "你"}
data: {"token": "好"}
data: {"done": true}
```

## 配置

详见 `config.yaml`，包含配额限制、上下文窗口、模型选择、检索参数等。
