import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path != "/api/chat":
            return await call_next(request)

        client_ip = request.client.host
        redis = request.app.state.redis
        key = f"quota:ip:{client_ip}"
        now = time.time()
        window = 60  # 1 minute

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        request_count = results[2]

        if request_count > settings.quota.ip_rate_limit:
            return JSONResponse(
                status_code=429,
                content={"error": "IP rate limit exceeded"},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
