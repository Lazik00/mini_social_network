from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.core.time import utc_now
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.services.cleanup import CleanupService
from app.tasks import cleanup as cleanup_module
from tests.helpers import PRIMARY_USER, SECOND_USER, THIRD_USER


async def test_cleanup_deletes_only_expired_unverified_users(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    old = utc_now() - timedelta(hours=72)
    password_hash = hash_password(PRIMARY_USER["password"])

    async with session_maker() as session:
        session.add_all(
            [
                User(
                    email=PRIMARY_USER["email"],
                    username=PRIMARY_USER["username"],
                    full_name=PRIMARY_USER["full_name"],
                    password_hash=password_hash,
                    is_verified=False,
                    created_at=old,
                    updated_at=old,
                ),
                User(
                    email=SECOND_USER["email"],
                    username=SECOND_USER["username"],
                    full_name=SECOND_USER["full_name"],
                    password_hash=password_hash,
                    is_verified=True,
                    created_at=old,
                    updated_at=old,
                ),
                User(
                    email=THIRD_USER["email"],
                    username=THIRD_USER["username"],
                    full_name=THIRD_USER["full_name"],
                    password_hash=password_hash,
                    is_verified=False,
                ),
            ]
        )
        await session.commit()

    async with session_maker() as session:
        deleted_users = await CleanupService(session).delete_expired_unverified_users()
        assert deleted_users == 1

    async with session_maker() as session:
        users = (await session.execute(select(User))).scalars().all()
        emails = {user.email for user in users}

    assert PRIMARY_USER["email"] not in emails
    assert SECOND_USER["email"] in emails
    assert THIRD_USER["email"] in emails


async def test_post_ttl_cleanup_does_nothing_when_unset(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    old = utc_now() - timedelta(days=90)
    password_hash = hash_password(PRIMARY_USER["password"])

    async with session_maker() as session:
        user = User(
            email=PRIMARY_USER["email"],
            username=PRIMARY_USER["username"],
            full_name=PRIMARY_USER["full_name"],
            password_hash=password_hash,
            is_verified=True,
        )
        session.add(user)
        await session.flush()
        session.add(
            Post(
                author_id=user.id,
                title="Medicalka old post",
                content="This post remains when SOCIAL_POST_TTL_DAYS is unset.",
                created_at=old,
                updated_at=old,
            )
        )
        await session.commit()

    async with session_maker() as session:
        deleted_posts = await CleanupService(session).delete_expired_posts()
        assert deleted_posts == 0

    async with session_maker() as session:
        posts = (await session.execute(select(Post))).scalars().all()

    assert len(posts) == 1


async def test_post_ttl_cleanup_deletes_old_posts_and_cascades(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    old = utc_now() - timedelta(days=90)
    password_hash = hash_password(PRIMARY_USER["password"])

    async with session_maker() as session:
        laziz = User(
            email=PRIMARY_USER["email"],
            username=PRIMARY_USER["username"],
            full_name=PRIMARY_USER["full_name"],
            password_hash=password_hash,
            is_verified=True,
        )
        lazizbek = User(
            email=SECOND_USER["email"],
            username=SECOND_USER["username"],
            full_name=SECOND_USER["full_name"],
            password_hash=password_hash,
            is_verified=True,
        )
        session.add_all([laziz, lazizbek])
        await session.flush()

        old_post = Post(
            author_id=laziz.id,
            title="Medicalka old post",
            content="This post should be removed by TTL cleanup.",
            created_at=old,
            updated_at=old,
        )
        fresh_post = Post(
            author_id=laziz.id,
            title="Medicalka fresh post",
            content="This post should remain after TTL cleanup.",
        )
        session.add_all([old_post, fresh_post])
        await session.flush()

        session.add_all(
            [
                Comment(
                    post_id=old_post.id,
                    author_id=lazizbek.id,
                    content="Lazizbek comment on the old Medicalka post.",
                ),
                Like(user_id=lazizbek.id, post_id=old_post.id),
            ]
        )
        await session.commit()

    async with session_maker() as session:
        deleted_posts = await CleanupService(session).delete_expired_posts(ttl_days=30)
        assert deleted_posts == 1

    async with session_maker() as session:
        posts = (await session.execute(select(Post))).scalars().all()
        comments = (await session.execute(select(Comment))).scalars().all()
        likes = (await session.execute(select(Like))).scalars().all()

    assert [post.title for post in posts] == ["Medicalka fresh post"]
    assert comments == []
    assert likes == []


def test_celery_cleanup_task_calls_cleanup_service(monkeypatch) -> None:
    calls = {"count": 0}

    async def fake_cleanup() -> int:
        calls["count"] += 1
        return 3

    monkeypatch.setattr(
        cleanup_module,
        "run_cleanup_expired_unverified_users",
        fake_cleanup,
    )

    result = cleanup_module.cleanup_expired_unverified_users_task.run()

    assert result == {"deleted_users": 3}
    assert calls["count"] == 1


def test_celery_post_cleanup_task_calls_cleanup_service(monkeypatch) -> None:
    calls = {"count": 0}

    async def fake_cleanup() -> int:
        calls["count"] += 1
        return 2

    monkeypatch.setattr(
        cleanup_module,
        "run_cleanup_expired_posts",
        fake_cleanup,
    )

    result = cleanup_module.cleanup_expired_posts_task.run()

    assert result == {"deleted_posts": 2}
    assert calls["count"] == 1
