from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.time import utc_now
from app.models.email_verification_token import EmailVerificationToken
from app.services.verification import VerificationService
from tests.helpers import PRIMARY_USER, register_user


async def test_verification_token_is_returned_on_registration(
    client: AsyncClient,
) -> None:
    registration = await register_user(client, PRIMARY_USER)

    assert registration["verification_token"]


async def test_valid_token_verifies_user(client: AsyncClient) -> None:
    registration = await register_user(client, PRIMARY_USER)

    response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": registration["verification_token"]},
    )

    assert response.status_code == 200
    assert response.json()["is_verified"] is True


async def test_used_token_cannot_be_reused(client: AsyncClient) -> None:
    registration = await register_user(client, PRIMARY_USER)
    token = registration["verification_token"]

    first_response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": token},
    )
    second_response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": token},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["success"] is False


async def test_invalid_token_returns_error(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": "invalid-laziz-verification-token"},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


async def test_expired_token_returns_error(
    client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    registration = await register_user(client, PRIMARY_USER)
    token_hash = VerificationService.hash_token(registration["verification_token"])

    async with session_maker() as session:
        db_token = (
            await session.execute(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.token_hash == token_hash
                )
            )
        ).scalar_one()
        db_token.expires_at = utc_now() - timedelta(hours=1)
        await session.commit()

    response = await client.get(
        "/api/v1/auth/verify-email",
        params={"token": registration["verification_token"]},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
