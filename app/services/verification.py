import hashlib
import logging
import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestError
from app.core.time import ensure_aware, utc_now
from app.models.user import User
from app.repositories.verification_tokens import VerificationTokenRepository

logger = logging.getLogger(__name__)


class VerificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tokens = VerificationTokenRepository(session)
        self.settings = get_settings()

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create_token_for_user(self, user: User) -> str:
        raw_token = secrets.token_urlsafe(32)
        now = utc_now()
        await self.tokens.invalidate_unused_tokens_for_user(
            user_id=user.id,
            used_at=now,
        )
        await self.tokens.create(
            user_id=user.id,
            token_hash=self.hash_token(raw_token),
            expires_at=now
            + timedelta(hours=self.settings.verification_token_expire_hours),
        )
        logger.info("Created email verification token for user_id=%s", user.id)
        return raw_token

    async def verify_email(self, raw_token: str) -> User:
        token = await self.tokens.get_by_hash_with_user(self.hash_token(raw_token))
        if token is None:
            raise BadRequestError("Invalid verification token")
        if token.used_at is not None:
            raise BadRequestError("Verification token has already been used")
        if ensure_aware(token.expires_at) < utc_now():
            raise BadRequestError("Verification token has expired")

        now = utc_now()
        token.user.is_verified = True
        token.used_at = now
        await self.tokens.invalidate_unused_tokens_for_user(
            user_id=token.user_id,
            used_at=now,
        )
        await self.session.commit()
        logger.info("Verified email for user_id=%s", token.user_id)
        return token.user
