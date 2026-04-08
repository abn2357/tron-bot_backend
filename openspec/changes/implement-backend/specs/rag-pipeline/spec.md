## ADDED Requirements

### Requirement: Question rewriting
系统 SHALL 使用 Claude Sonnet 对用户原始提问进行重写，结合历史上下文生成更适合检索的查询。

#### Scenario: Rewrite with context
- **WHEN** 用户提问 "那第二个呢" 且历史上下文涉及某个列表
- **THEN** Sonnet 将其重写为包含具体指代的完整问题

#### Scenario: Standalone question
- **WHEN** 用户提问已经是完整的独立问题，无需上下文补全
- **THEN** Sonnet 返回优化后的查询（可能与原文相近）

### Requirement: Text embedding
系统 SHALL 使用本地 bge-base-zh-v1.5 模型将重写后的问题转为 768 维向量。

#### Scenario: Embed rewritten question
- **WHEN** 收到重写后的问题文本
- **THEN** 返回 768 维浮点向量

### Requirement: Vector retrieval
系统 SHALL 使用 Chroma 向量库进行语义检索，返回最相关的文档片段。

#### Scenario: Relevant documents found
- **WHEN** 向量检索找到相似度高于 score_threshold 的文档
- **THEN** 返回最多 top_k 个片段，按相似度降序排列

#### Scenario: No relevant documents found
- **WHEN** 所有文档的相似度均低于 score_threshold
- **THEN** 返回空列表，生成阶段基于通用知识回答

### Requirement: Answer generation
系统 SHALL 使用 Claude Opus 基于检索到的文档片段和对话上下文，流式生成回答。

#### Scenario: Generate with retrieved context
- **WHEN** 检索返回了相关片段
- **THEN** Opus 基于片段内容生成回答，以 SSE 流式输出

#### Scenario: Generate without retrieved context
- **WHEN** 检索未返回相关片段
- **THEN** Opus 基于对话上下文和通用知识生成回答，并提示用户该回答可能不基于知识库
