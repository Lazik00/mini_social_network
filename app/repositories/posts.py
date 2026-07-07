from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import PaginationParams
from app.models.post import Post
from app.models.user import User


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def build_filters(
        *,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[object]:
        filters: list[object] = []
        if search:
            pattern = f"%{search}%"
            filters.append(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))
        if date_from:
            filters.append(Post.created_at >= date_from)
        if date_to:
            filters.append(Post.created_at <= date_to)
        return filters

    async def create(self, *, author_id: UUID, title: str, content: str) -> Post:
        post = Post(author_id=author_id, title=title, content=content)
        self.session.add(post)
        await self.session.flush()
        return post

    async def get_by_id(
        self, post_id: UUID, *, with_details: bool = False
    ) -> Post | None:
        stmt = select(Post).where(Post.id == post_id)
        if with_details:
            stmt = stmt.options(
                selectinload(Post.comments),
                selectinload(Post.likes),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_posts(
        self,
        *,
        pagination: PaginationParams,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[list[Post], int]:
        filters = self.build_filters(
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        count_stmt = select(func.count()).select_from(Post).where(*filters)
        total = await self.session.scalar(count_stmt)

        stmt = (
            select(Post)
            .options(selectinload(Post.comments), selectinload(Post.likes))
            .where(*filters)
            .order_by(Post.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all()), int(total or 0)

    async def list_feed_users(
        self,
        *,
        pagination: PaginationParams,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[list[User], int]:
        filters = self.build_filters(
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        user_has_posts = exists(
            select(Post.id).where(Post.author_id == User.id, *filters)
        )

        count_stmt = select(func.count()).select_from(User).where(user_has_posts)
        total = await self.session.scalar(count_stmt)

        posts_loader = (
            selectinload(User.posts.and_(*filters))
            if filters
            else selectinload(User.posts)
        )
        stmt = (
            select(User)
            .where(user_has_posts)
            .options(posts_loader.selectinload(Post.likes))
            .order_by(User.username.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all()), int(total or 0)

    async def update(
        self,
        post: Post,
        *,
        title: str | None,
        content: str | None,
    ) -> Post:
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        await self.session.flush()
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.flush()
