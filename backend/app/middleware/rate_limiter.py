import time

from fastapi import Request
from redis.asyncio import Redis

from app.config.redis import get_redis
from app.config.settings import settings
from app.utils.exceptions import RateLimitException


class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path}"

        # Get redis inline by iterating generator once
        redis_gen = get_redis()
        redis: Redis = await anext(redis_gen)

        now = time.time()
        pipeline = redis.pipeline()

        # Sliding window using sorted sets
        await pipeline.zremrangebyscore(key, 0, now - self.window)
        await pipeline.zadd(key, {str(now): now})
        await pipeline.zcard(key)
        await pipeline.expire(key, self.window)

        results = await pipeline.execute()
        request_count = results[2]

        if request_count > self.requests:
            raise RateLimitException()


def rate_limit(
    max_requests: int = settings.RATE_LIMIT_REQUESTS,
    window_seconds: int = settings.RATE_LIMIT_WINDOW_SECONDS,
) -> RateLimiter:
    return RateLimiter(requests=max_requests, window=window_seconds)
