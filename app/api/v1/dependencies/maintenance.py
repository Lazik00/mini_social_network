from typing import Annotated

from fastapi import Header

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError


async def require_maintenance_token(
    x_maintenance_token: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    expected = settings.maintenance_token
    if expected is None:
        raise ForbiddenError("Maintenance endpoint is not configured")
    if x_maintenance_token != expected.get_secret_value():
        raise ForbiddenError("Invalid maintenance token")
