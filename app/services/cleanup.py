import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.time import utc_now
from app.repositories.posts import PostRepository
from app.repositories.users import UserRepository

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.posts = PostRepository(session)
        self.settings = get_settings()

    async def delete_expired_unverified_users(self) -> int:
        cutoff = utc_now() - timedelta(
            hours=self.settings.cleanup_unverified_after_hours
        )
        deleted_users = await self.users.delete_unverified_created_before(cutoff)
        await self.session.commit()
        logger.info("Deleted %s expired unverified users", deleted_users)
        return deleted_users

    async def delete_expired_posts(self, *, ttl_days: int | None = None) -> int:
        resolved_ttl_days = (
            ttl_days if ttl_days is not None else self.settings.post_ttl_days
        )
        if resolved_ttl_days is None:
            logger.info(
                "Post TTL cleanup skipped because SOCIAL_POST_TTL_DAYS is unset"
            )
            return 0

        cutoff = utc_now() - timedelta(days=resolved_ttl_days)
        deleted_posts = await self.posts.delete_created_before(cutoff)
        await self.session.commit()
        logger.info("Deleted %s expired posts", deleted_posts)
        return deleted_posts
