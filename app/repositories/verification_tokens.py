from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.email_verification_token import EmailVerificationToken


class VerificationTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_hash_with_user(
        self,
        token_hash: str,
    ) -> EmailVerificationToken | None:
        result = await self.session.execute(
            select(EmailVerificationToken)
            .options(selectinload(EmailVerificationToken.user))
            .where(EmailVerificationToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def invalidate_unused_tokens_for_user(
        self,
        *,
        user_id: UUID,
        used_at: datetime,
    ) -> None:
        await self.session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
            )
            .values(used_at=used_at)
        )
