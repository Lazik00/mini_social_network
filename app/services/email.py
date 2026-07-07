import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send_verification_email(self, *, email: str, token: str) -> None:
        """Send a verification token or link to the user."""


class LoggingEmailSender:
    async def send_verification_email(self, *, email: str, token: str) -> None:
        _ = token
        logger.info("Email verification message prepared for email=%s", email)


class SMTPEmailSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_verification_email(self, *, email: str, token: str) -> None:
        await asyncio.to_thread(self._send_verification_email, email=email, token=token)
        logger.info("Verification email sent via SMTP to email=%s", email)

    def _send_verification_email(self, *, email: str, token: str) -> None:
        verification_url = (
            f"{self.settings.public_base_url.rstrip('/')}/api/v1/auth/verify-email?"
            f"{urlencode({'token': token})}"
        )
        message = EmailMessage()
        message["Subject"] = "Verify your Mini Social Network account"
        message["From"] = self.settings.smtp_from_email or ""
        message["To"] = email
        message.set_content(
            "Welcome to Mini Social Network.\n\n"
            f"Verify your email using this link:\n{verification_url}\n\n"
            "If you did not register, ignore this email."
        )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                smtp.login(
                    self.settings.smtp_username,
                    self.settings.smtp_password.get_secret_value(),
                )
            smtp.send_message(message)


def get_email_sender(settings: Settings | None = None) -> EmailSender:
    resolved_settings = settings or get_settings()
    smtp_configured = bool(
        resolved_settings.smtp_host
        and resolved_settings.smtp_from_email
        and resolved_settings.smtp_port
    )
    if smtp_configured:
        return SMTPEmailSender(resolved_settings)
    return LoggingEmailSender()
