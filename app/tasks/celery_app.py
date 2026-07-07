from celery import Celery

from app.core.config import get_settings

settings = get_settings()
beat_schedule = {
    "cleanup-expired-unverified-users-hourly": {
        "task": "cleanup_expired_unverified_users",
        "schedule": 60 * 60,
    },
}

if settings.post_ttl_days is not None:
    beat_schedule["cleanup-expired-posts-daily"] = {
        "task": "cleanup_expired_posts",
        "schedule": 24 * 60 * 60,
    }

celery_app = Celery(
    "mini_social_network",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule=beat_schedule,
)
