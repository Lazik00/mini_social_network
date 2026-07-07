from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        email: str,
        username: str,
        full_name: str,
        password_hash: str,
    ) -> User:
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            is_verified=False,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        user: User,
        *,
        username: str | None,
        full_name: str | None,
    ) -> User:
        if username is not None:
            user.username = username
        if full_name is not None:
            user.full_name = full_name
        await self.session.flush()
        return user

    async def delete_unverified_created_before(self, cutoff: datetime) -> int:
        result = await self.session.execute(
            delete(User).where(
                User.is_verified.is_(False),
                User.created_at < cutoff,
            )
        )
        return int(result.rowcount or 0)
