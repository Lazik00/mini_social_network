from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import get_settings
from app.services.rate_limit import LoginRateLimiter, RedisLoginRateLimiter


async def get_login_rate_limiter() -> AsyncGenerator[LoginRateLimiter]:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield RedisLoginRateLimiter(
            redis,
            max_attempts=settings.login_rate_limit_attempts,
            window_seconds=settings.login_rate_limit_window_seconds,
        )
    finally:
        await redis.aclose()
