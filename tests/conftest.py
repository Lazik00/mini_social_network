import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SOCIAL_APP_NAME", "Test Social Network")
os.environ.setdefault("SOCIAL_ENVIRONMENT", "test")
os.environ.setdefault("SOCIAL_DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("SOCIAL_REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("SOCIAL_JWT_SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("SOCIAL_MAINTENANCE_TOKEN", "test-maintenance-token")
os.environ.setdefault("SOCIAL_CLEANUP_UNVERIFIED_AFTER_HOURS", "48")

from app import models  # noqa: E402,F401
from app.api.v1.dependencies.rate_limit import get_login_rate_limiter  # noqa: E402
from app.core.exceptions import TooManyRequestsError  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import create_app  # noqa: E402


class InMemoryLoginRateLimiter:
    def __init__(self, max_attempts: int = 5) -> None:
        self.max_attempts = max_attempts
        self.attempts: dict[tuple[str, str], int] = {}

    @staticmethod
    def key(*, ip_address: str, identifier: str) -> tuple[str, str]:
        return ip_address, identifier.lower()

    async def ensure_allowed(self, *, ip_address: str, identifier: str) -> None:
        key = self.key(ip_address=ip_address, identifier=identifier)
        if self.attempts.get(key, 0) >= self.max_attempts:
            raise TooManyRequestsError("Too many failed login attempts")

    async def record_failure(self, *, ip_address: str, identifier: str) -> None:
        key = self.key(ip_address=ip_address, identifier=identifier)
        self.attempts[key] = self.attempts.get(key, 0) + 1

    async def reset(self, *, ip_address: str, identifier: str) -> None:
        self.attempts.pop(self.key(ip_address=ip_address, identifier=identifier), None)


@pytest.fixture
def login_rate_limiter() -> InMemoryLoginRateLimiter:
    return InMemoryLoginRateLimiter()


@pytest_asyncio.fixture
async def session_maker() -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    yield maker

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    session_maker: async_sessionmaker[AsyncSession],
    login_rate_limiter: InMemoryLoginRateLimiter,
) -> AsyncGenerator[AsyncClient]:
    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_login_rate_limiter] = lambda: login_rate_limiter
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
