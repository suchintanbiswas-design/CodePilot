import logging
from typing import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config.settings import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def init_redis():
    global _redis_client
    logger.info("Initializing Redis connection...")
    _redis_client = aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )


async def close_redis():
    global _redis_client
    if _redis_client:
        logger.info("Closing Redis connection...")
        await _redis_client.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    if not _redis_client:
        await init_redis()
    yield _redis_client
