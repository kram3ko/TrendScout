from functools import cache

from redis.asyncio import Redis

from app.core.config import get_settings


@cache
def get_redis() -> Redis:
    """Shared client — one connection pool per process."""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)
