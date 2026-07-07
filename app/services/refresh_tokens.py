import hashlib
import logging
import secrets
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.time import ensure_aware, utc_now
from app.models.user import User
from app.repositories.refresh_tokens import RefreshTokenRepository

logger = logging.getLogger(__name__)


class RefreshTokenService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tokens = RefreshTokenRepository(session)
        self.settings = get_settings()

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create_token_for_user(self, user: User) -> str:
        raw_token = secrets.token_urlsafe(64)
        await self.tokens.create(
            user_id=user.id,
            token_hash=self.hash_token(raw_token),
            expires_at=utc_now()
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        logger.info("Created refresh token for user_id=%s", user.id)
        return raw_token

    async def rotate_token(self, raw_token: str) -> tuple[User, str]:
        token = await self.tokens.get_by_hash_with_user(self.hash_token(raw_token))
        if token is None:
            raise UnauthorizedError("Invalid refresh token")
        if token.revoked_at is not None:
            raise UnauthorizedError("Refresh token has been revoked")
        if ensure_aware(token.expires_at) < utc_now():
            token.revoked_at = utc_now()
            await self.session.commit()
            raise UnauthorizedError("Refresh token has expired")

        token.revoked_at = utc_now()
        new_refresh_token = await self.create_token_for_user(token.user)
        logger.info("Rotated refresh token for user_id=%s", token.user_id)
        return token.user, new_refresh_token
