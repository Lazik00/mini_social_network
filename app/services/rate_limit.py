import hashlib
from typing import Protocol

from redis.asyncio import Redis

from app.core.exceptions import TooManyRequestsError


class LoginRateLimiter(Protocol):
    async def ensure_allowed(self, *, ip_address: str, identifier: str) -> None:
        """Raise when the login attempt should be rejected."""

    async def record_failure(self, *, ip_address: str, identifier: str) -> None:
        """Store one failed login attempt."""

    async def reset(self, *, ip_address: str, identifier: str) -> None:
        """Clear failures after a successful login."""


class RedisLoginRateLimiter:
    def __init__(
        self,
        redis: Redis,
        *,
        max_attempts: int,
        window_seconds: int,
    ) -> None:
        self.redis = redis
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    @staticmethod
    def build_key(*, ip_address: str, identifier: str) -> str:
        digest = hashlib.sha256(
            f"{ip_address}:{identifier.lower()}".encode()
        ).hexdigest()
        return f"login_failures:{digest}"

    async def ensure_allowed(self, *, ip_address: str, identifier: str) -> None:
        key = self.build_key(ip_address=ip_address, identifier=identifier)
        attempts = await self.redis.get(key)
        if attempts is not None and int(attempts) >= self.max_attempts:
            raise TooManyRequestsError("Too many failed login attempts")

    async def record_failure(self, *, ip_address: str, identifier: str) -> None:
        key = self.build_key(ip_address=ip_address, identifier=identifier)
        attempts = await self.redis.incr(key)
        if attempts == 1:
            await self.redis.expire(key, self.window_seconds)

    async def reset(self, *, ip_address: str, identifier: str) -> None:
        key = self.build_key(ip_address=ip_address, identifier=identifier)
        await self.redis.delete(key)
