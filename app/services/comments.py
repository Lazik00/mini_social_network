from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.comments import CommentRepository
from app.repositories.posts import PostRepository
from app.schemas.comments import CommentCreate, CommentRead
from app.services.mappers import comment_to_read
from app.services.permissions import ensure_owner, ensure_verified


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.posts = PostRepository(session)

    async def list_comments(self, post_id: UUID) -> list[CommentRead]:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        comments = await self.comments.list_by_post(post_id)
        return [comment_to_read(comment) for comment in comments]

    async def create_comment(
        self,
        *,
        post_id: UUID,
        user: User,
        data: CommentCreate,
    ) -> CommentRead:
        ensure_verified(user)
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")

        comment = await self.comments.create(
            post_id=post_id,
            author_id=user.id,
            content=data.content,
        )
        await self.session.commit()
        return comment_to_read(comment)

    async def delete_comment(
        self,
        *,
        post_id: UUID,
        comment_id: UUID,
        user: User,
    ) -> None:
        ensure_verified(user)
        comment = await self.comments.get_by_id(comment_id)
        if comment is None or comment.post_id != post_id:
            raise NotFoundError("Comment not found")
        ensure_owner(comment.author_id, user)
        await self.comments.delete(comment)
        await self.session.commit()
