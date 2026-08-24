from redis.asyncio import Redis

LOGIN_ATTEMPT_KEY = "login:attempts:{username}"
MAX_ATTEMPTS = 10
WINDOW_SECONDS = 300


class LoginRateLimiter:
    """Fixed window per username — blunts credential stuffing on the only public endpoint."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def register_attempt(self, username: str) -> None:
        key = LOGIN_ATTEMPT_KEY.format(username=username.lower())
        attempts = await self._redis.incr(key)
        if attempts == 1:
            await self._redis.expire(key, WINDOW_SECONDS)

    async def is_blocked(self, username: str) -> bool:
        attempts = await self._redis.get(LOGIN_ATTEMPT_KEY.format(username=username.lower()))
        return attempts is not None and int(attempts) > MAX_ATTEMPTS

    async def reset(self, username: str) -> None:
        await self._redis.delete(LOGIN_ATTEMPT_KEY.format(username=username.lower()))
