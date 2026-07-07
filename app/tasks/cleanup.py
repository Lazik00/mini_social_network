import asyncio
import logging

from app.db.session import async_session_maker
from app.services.cleanup import CleanupService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def run_cleanup_expired_unverified_users() -> int:
    async with async_session_maker() as session:
        return await CleanupService(session).delete_expired_unverified_users()


async def run_cleanup_expired_posts() -> int:
    async with async_session_maker() as session:
        return await CleanupService(session).delete_expired_posts()


@celery_app.task(
    name="cleanup_expired_unverified_users",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def cleanup_expired_unverified_users_task() -> dict[str, int]:
    deleted_users = asyncio.run(run_cleanup_expired_unverified_users())
    logger.info("Cleanup task completed deleted_users=%s", deleted_users)
    return {"deleted_users": deleted_users}


@celery_app.task(
    name="cleanup_expired_posts",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def cleanup_expired_posts_task() -> dict[str, int]:
    deleted_posts = asyncio.run(run_cleanup_expired_posts())
    logger.info("Post cleanup task completed deleted_posts=%s", deleted_posts)
    return {"deleted_posts": deleted_posts}
