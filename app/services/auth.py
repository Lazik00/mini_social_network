import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.users import UserCreate
from app.services.email import EmailSender, get_email_sender
from app.services.rate_limit import LoginRateLimiter
from app.services.verification import VerificationService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        email_sender: EmailSender | None = None,
    ) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.verification = VerificationService(session)
        self.email_sender = email_sender or get_email_sender()

    async def register(self, data: UserCreate) -> tuple[User, str]:
        email = str(data.email).lower()
        if await self.users.get_by_email(email):
            raise ConflictError("User with this email already exists")
        if await self.users.get_by_username(data.username):
            raise ConflictError("User with this username already exists")

        try:
            user = await self.users.create(
                email=email,
                username=data.username,
                full_name=data.full_name,
                password_hash=hash_password(data.password),
            )
            verification_token = await self.verification.create_token_for_user(user)
            await self.email_sender.send_verification_email(
                email=user.email,
                token=verification_token,
            )
            await self.session.commit()
            logger.info("Registered user_id=%s", user.id)
            return user, verification_token
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "User with this email or username already exists"
            ) from exc

    async def login(
        self,
        data: LoginRequest,
        *,
        ip_address: str,
        rate_limiter: LoginRateLimiter,
    ) -> str:
        identifier = str(data.email).lower() if data.email else data.username
        if identifier is None:
            raise UnauthorizedError("Invalid credentials")

        await rate_limiter.ensure_allowed(
            ip_address=ip_address,
            identifier=identifier,
        )

        user = None
        if data.email:
            user = await self.users.get_by_email(str(data.email).lower())
        if data.username:
            user = await self.users.get_by_username(data.username)

        if user is None or not verify_password(data.password, user.password_hash):
            await rate_limiter.record_failure(
                ip_address=ip_address,
                identifier=identifier,
            )
            logger.info("Failed login attempt")
            raise UnauthorizedError("Invalid credentials")

        await rate_limiter.reset(ip_address=ip_address, identifier=identifier)
        logger.info("Successful login for user_id=%s", user.id)
        return create_access_token(user.id)
