from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        post_id: UUID,
        author_id: UUID,
        content: str,
    ) -> Comment:
        comment = Comment(post_id=post_id, author_id=author_id, content=content)
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        result = await self.session.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_post(self, post_id: UUID) -> list[Comment]:
        result = await self.session.execute(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete(self, comment: Comment) -> None:
        await self.session.delete(comment)
        await self.session.flush()
