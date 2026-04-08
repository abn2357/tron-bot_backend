## ADDED Requirements

### Requirement: YAML configuration file
系统 SHALL 从 config.yaml 文件加载运行时配置，包括配额、上下文、模型、检索、Redis、服务器等参数。

#### Scenario: Load valid config
- **WHEN** config.yaml 存在且格式正确
- **THEN** 系统加载所有配置项并启动

#### Scenario: Config file missing
- **WHEN** config.yaml 不存在
- **THEN** 系统使用内置默认值启动并输出警告日志

### Requirement: Environment variable override
系统 SHALL 支持通过环境变量覆盖配置项，环境变量优先级高于 config.yaml。

#### Scenario: Override API key via environment
- **WHEN** 环境变量 ANTHROPIC_API_KEY 已设置
- **THEN** 系统使用该环境变量的值，而非 config.yaml 中的值

### Requirement: Configuration validation
系统 SHALL 在启动时校验配置项的有效性。

#### Scenario: Invalid quota value
- **WHEN** user_daily_limit 配置为负数
- **THEN** 系统拒绝启动并输出明确的错误信息
