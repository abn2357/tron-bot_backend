import os
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class QuotaConfig(BaseModel):
    ip_rate_limit: int = 30
    user_daily_limit: int = 50
    user_session_limit: int = 20

    @field_validator("ip_rate_limit", "user_daily_limit", "user_session_limit")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be a positive integer")
        return v


class ContextConfig(BaseModel):
    max_history_turns: int = 10
    max_context_tokens: int = 4000


class ModelsConfig(BaseModel):
    rewriter: str = "claude-sonnet-4-20250514"
    generator: str = "claude-opus-4-20250514"
    embedding: str = "BAAI/bge-base-zh-v1.5"


class RetrievalConfig(BaseModel):
    top_k: int = 5
    score_threshold: float = 0.5


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"
    history_ttl: int = 86400
    quota_ttl: int = 86400


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]


class AppConfig(BaseModel):
    quota: QuotaConfig = QuotaConfig()
    context: ContextConfig = ContextConfig()
    models: ModelsConfig = ModelsConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    redis: RedisConfig = RedisConfig()
    server: ServerConfig = ServerConfig()


def load_config(path: str = "config.yaml") -> AppConfig:
    data = {}
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        import logging
        logging.warning(f"Config file {path} not found, using defaults")

    # Environment variable overrides
    if os.environ.get("REDIS_URL"):
        data.setdefault("redis", {})["url"] = os.environ["REDIS_URL"]
    if os.environ.get("SERVER_PORT"):
        data.setdefault("server", {})["port"] = int(os.environ["SERVER_PORT"])
    if os.environ.get("CORS_ORIGINS"):
        data.setdefault("server", {})["cors_origins"] = os.environ["CORS_ORIGINS"].split(",")

    return AppConfig(**data)


settings = load_config()
