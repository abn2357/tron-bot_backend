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
- Chroma 向量库已构建（见下方「构建向量库」）
- Anthropic API Key

### 安装并启动 Redis（macOS）

```bash
brew install redis
brew services start redis
redis-cli ping  # 返回 PONG 表示正常
```

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 构建向量库

从 [tronprotocol/documentation-zh](https://github.com/tronprotocol/documentation-zh) 自动拉取文档，按 mkdocs.yml 中 nav 列出的文件进行分块、向量化，写入 Chroma。

```bash
python scripts/build_vectordb.py
```

脚本会自动克隆文档仓库到 `./documentation-zh`，后续再运行会自动拉取最新版本。构建完成后向量库位于 `./chroma_db`。

可选参数：
- `--skip-clone`：跳过 git clone/pull，直接使用本地已有的文档仓库
- `--repo-dir <path>`：指定文档仓库本地路径
- `--chroma-path <path>`：指定向量库输出路径

### 启动服务

```bash
export ANTHROPIC_AUTH_TOKEN=your_key
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_AUTH_TOKEN` | Claude API 密钥 | 无（必填） |
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
