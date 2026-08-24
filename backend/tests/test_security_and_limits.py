from unittest.mock import AsyncMock

from app.auth.ratelimit import LOGIN_ATTEMPT_KEY, LoginRateLimiter
from app.core.security import hash_password, issue_token, read_token, verify_password


def test_password_hash_and_token_round_trip() -> None:
    password_hash = hash_password("admin123")
    token = issue_token("admin")

    assert verify_password("admin123", password_hash) is True
    assert verify_password("wrong", password_hash) is False
    assert read_token(token) == "admin"
    assert read_token("forged") is None


async def test_rate_limiter_sets_window_and_resets_username() -> None:
    redis = SimpleRedis(incremented=1)
    limiter = LoginRateLimiter(redis)

    await limiter.register_attempt("Admin")
    await limiter.reset("Admin")

    key = LOGIN_ATTEMPT_KEY.format(username="admin")
    redis.incr.assert_awaited_once_with(key)
    redis.expire.assert_awaited_once()
    redis.delete.assert_awaited_once_with(key)


async def test_rate_limiter_blocks_after_limit() -> None:
    redis = SimpleRedis(current=b"11")
    limiter = LoginRateLimiter(redis)

    assert await limiter.is_blocked("Admin") is True
    redis.get.assert_awaited_once_with(LOGIN_ATTEMPT_KEY.format(username="admin"))


class SimpleRedis:
    def __init__(self, incremented: int = 0, current=None) -> None:
        self.incr = AsyncMock(return_value=incremented)
        self.expire = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock(return_value=current)
