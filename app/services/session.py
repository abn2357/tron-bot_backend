import json

from redis.asyncio import Redis

from app.config import settings


class QuotaExceeded(Exception):
    def __init__(self, message: str):
        self.message = message


async def check_quota(redis: Redis, fingerprint: str, session_id: str) -> None:
    """Check user daily quota and session turn limit. Raises QuotaExceeded if exceeded."""
    # Check daily quota by fingerprint
    daily_key = f"quota:user:{fingerprint}"
    daily_count = await redis.get(daily_key)
    if daily_count is not None and int(daily_count) >= settings.quota.user_daily_limit:
        raise QuotaExceeded("Daily quota exceeded. Please try again tomorrow.")

    # Check session turn limit
    history_key = f"history:{session_id}"
    turn_count = await redis.llen(history_key)
    # Each turn = 2 entries (user + assistant)
    if turn_count // 2 >= settings.quota.user_session_limit:
        raise QuotaExceeded("Session limit reached. Please start a new session.")

    # Increment daily counter
    pipe = redis.pipeline()
    pipe.incr(daily_key)
    pipe.expire(daily_key, settings.redis.quota_ttl)
    await pipe.execute()


async def load_history(redis: Redis, session_id: str) -> list[dict]:
    """Load recent conversation history from Redis."""
    history_key = f"history:{session_id}"
    max_entries = settings.context.max_history_turns * 2  # user + assistant per turn

    raw_entries = await redis.lrange(history_key, -max_entries, -1)
    return [json.loads(entry) for entry in raw_entries]


async def save_history(redis: Redis, session_id: str, question: str, answer: str) -> None:
    """Save a Q&A turn to Redis conversation history."""
    history_key = f"history:{session_id}"
    pipe = redis.pipeline()
    pipe.rpush(history_key, json.dumps({"role": "user", "content": question}, ensure_ascii=False))
    pipe.rpush(history_key, json.dumps({"role": "assistant", "content": answer}, ensure_ascii=False))
    pipe.expire(history_key, settings.redis.history_ttl)
    await pipe.execute()
