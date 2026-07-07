from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.likes import LikeRepository
from app.repositories.posts import PostRepository
from app.schemas.likes import LikeRead


class LikeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.likes = LikeRepository(session)
        self.posts = PostRepository(session)

    async def like_post(self, *, post_id: UUID, user: User) -> LikeRead:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        if post.author_id == user.id:
            raise ForbiddenError("Users cannot like their own posts")
        if await self.likes.get_by_user_and_post(user_id=user.id, post_id=post_id):
            raise ConflictError("Post is already liked by this user")

        try:
            like = await self.likes.create(user_id=user.id, post_id=post_id)
            await self.session.commit()
            return LikeRead.model_validate(like)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Post is already liked by this user") from exc

    async def unlike_post(self, *, post_id: UUID, user: User) -> None:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        like = await self.likes.get_by_user_and_post(user_id=user.id, post_id=post_id)
        if like is None:
            raise NotFoundError("Like not found")
        await self.likes.delete(like)
        await self.session.commit()
