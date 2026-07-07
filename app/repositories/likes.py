from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: UUID, post_id: UUID) -> Like:
        like = Like(user_id=user_id, post_id=post_id)
        self.session.add(like)
        await self.session.flush()
        return like

    async def get_by_user_and_post(
        self,
        *,
        user_id: UUID,
        post_id: UUID,
    ) -> Like | None:
        result = await self.session.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, like: Like) -> None:
        await self.session.delete(like)
        await self.session.flush()
