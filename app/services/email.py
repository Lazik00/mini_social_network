import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send_verification_email(self, *, email: str, token: str) -> None:
        """Send a verification token or link to the user."""


class LoggingEmailSender:
    async def send_verification_email(self, *, email: str, token: str) -> None:
        _ = token
        logger.info("Email verification message prepared for email=%s", email)
