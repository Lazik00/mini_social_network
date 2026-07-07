from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.models.user import User
from app.repositories.posts import PostRepository
from app.schemas.posts import FeedUserItem, PostCreate, PostDetail, PostRead, PostUpdate
from app.services.mappers import post_to_detail, post_to_read, user_to_feed_item
from app.services.permissions import ensure_owner, ensure_verified


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.posts = PostRepository(session)

    @staticmethod
    def validate_date_range(
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> None:
        if date_from and date_to and date_from > date_to:
            raise BadRequestError("date_from must be earlier than or equal to date_to")

    async def list_posts(
        self,
        *,
        pagination: PaginationParams,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> PaginatedResponse[PostRead]:
        self.validate_date_range(date_from=date_from, date_to=date_to)
        posts, total = await self.posts.list_posts(
            pagination=pagination,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        return PaginatedResponse[PostRead](
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
            items=[post_to_read(post) for post in posts],
        )

    async def list_feed(
        self,
        *,
        pagination: PaginationParams,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> PaginatedResponse[FeedUserItem]:
        self.validate_date_range(date_from=date_from, date_to=date_to)
        users, total = await self.posts.list_feed_users(
            pagination=pagination,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        return PaginatedResponse[FeedUserItem](
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
            items=[user_to_feed_item(user) for user in users],
        )

    async def create_post(self, *, user: User, data: PostCreate) -> PostRead:
        ensure_verified(user)
        post = await self.posts.create(
            author_id=user.id,
            title=data.title,
            content=data.content,
        )
        await self.session.commit()
        return post_to_read(post)

    async def get_post_detail(self, post_id: UUID) -> PostDetail:
        post = await self.posts.get_by_id(post_id, with_details=True)
        if post is None:
            raise NotFoundError("Post not found")
        return post_to_detail(post)

    async def update_post(
        self,
        *,
        post_id: UUID,
        user: User,
        data: PostUpdate,
    ) -> PostRead:
        ensure_verified(user)
        post = await self.posts.get_by_id(post_id, with_details=True)
        if post is None:
            raise NotFoundError("Post not found")
        ensure_owner(post.author_id, user)
        post = await self.posts.update(post, title=data.title, content=data.content)
        await self.session.commit()
        return post_to_read(post)

    async def delete_post(self, *, post_id: UUID, user: User) -> None:
        ensure_verified(user)
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        ensure_owner(post.author_id, user)
        await self.posts.delete(post)
        await self.session.commit()
