## ADDED Requirements

### Requirement: Chat endpoint accepts questions via POST
系统 SHALL 提供 `POST /api/chat` 端点，接收 JSON 请求体包含 `question`（string）、`fingerprint`（string）、`session_id`（string）。

#### Scenario: Valid request
- **WHEN** 客户端发送包含 question、fingerprint、session_id 的 POST 请求到 /api/chat
- **THEN** 系统返回 200 状态码，Content-Type 为 text/event-stream

#### Scenario: Missing required fields
- **WHEN** 客户端发送缺少 question 字段的请求
- **THEN** 系统返回 422 状态码和错误信息

### Requirement: SSE streaming response
系统 SHALL 以 Server-Sent Events 格式流式返回生成结果，每个事件包含一个 token，最后发送 done 事件。

#### Scenario: Streaming tokens
- **WHEN** 请求处理成功进入生成阶段
- **THEN** 系统以 `data: {"token": "..."}` 格式逐 token 发送，结束时发送 `data: {"done": true}`

#### Scenario: Processing error during generation
- **WHEN** 生成过程中发生错误
- **THEN** 系统发送 `data: {"error": "..."}` 事件并关闭连接

### Requirement: IP rate limiting
系统 SHALL 对每个 IP 地址进行请求频率限制，超出限制时拒绝请求。

#### Scenario: Within rate limit
- **WHEN** 某 IP 在 1 分钟内请求次数未超过 ip_rate_limit 配置值
- **THEN** 请求正常处理

#### Scenario: Exceeding rate limit
- **WHEN** 某 IP 在 1 分钟内请求次数超过 ip_rate_limit 配置值
- **THEN** 系统返回 429 状态码和 Retry-After 头

### Requirement: CORS support
系统 SHALL 支持跨域请求，允许来自配置中指定 origins 的请求。

#### Scenario: Allowed origin
- **WHEN** 请求来自 cors_origins 配置中列出的域名
- **THEN** 响应包含正确的 CORS 头，请求正常处理
