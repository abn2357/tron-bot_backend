## ADDED Requirements

### Requirement: User quota check
系统 SHALL 基于用户指纹检查每日请求配额，超出配额时拒绝请求。

#### Scenario: Within daily quota
- **WHEN** 用户指纹当日请求次数未超过 user_daily_limit 配置值
- **THEN** 请求正常处理，配额计数 +1

#### Scenario: Exceeding daily quota
- **WHEN** 用户指纹当日请求次数已达 user_daily_limit
- **THEN** 系统返回 429 状态码，消息提示每日配额已用尽

### Requirement: Session turn limit
系统 SHALL 限制每个 Session 的最大对话轮数。

#### Scenario: Within session limit
- **WHEN** 当前 session_id 的对话轮数未超过 user_session_limit
- **THEN** 请求正常处理

#### Scenario: Exceeding session limit
- **WHEN** 当前 session_id 的对话轮数已达 user_session_limit
- **THEN** 系统返回 429 状态码，提示用户开始新会话

### Requirement: Conversation history loading
系统 SHALL 从 Redis 加载当前 session 的历史对话，截取最近 max_history_turns 轮，作为上下文传递给下游处理。

#### Scenario: Session with history
- **WHEN** Redis 中存在该 session_id 的对话记录
- **THEN** 加载最近 max_history_turns 轮对话作为上下文

#### Scenario: New session without history
- **WHEN** Redis 中不存在该 session_id 的记录
- **THEN** 上下文为空，请求正常继续

### Requirement: Conversation history saving
系统 SHALL 在生成完成后，将本轮问答写入 Redis 对话历史。

#### Scenario: Save after successful generation
- **WHEN** LLM 生成完成
- **THEN** 将用户提问和完整回答追加到 history:{session_id}，并设置 TTL
