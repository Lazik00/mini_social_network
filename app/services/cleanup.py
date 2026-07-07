import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.time import utc_now
from app.repositories.users import UserRepository

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.settings = get_settings()

    async def delete_expired_unverified_users(self) -> int:
        cutoff = utc_now() - timedelta(
            hours=self.settings.cleanup_unverified_after_hours
        )
        deleted_users = await self.users.delete_unverified_created_before(cutoff)
        await self.session.commit()
        logger.info("Deleted %s expired unverified users", deleted_users)
        return deleted_users
