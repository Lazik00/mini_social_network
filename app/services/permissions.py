from uuid import UUID

from app.core.exceptions import ForbiddenError
from app.models.user import User


def ensure_verified(user: User) -> None:
    if not user.is_verified:
        raise ForbiddenError("Email verification is required for this action")


def ensure_owner(owner_id: UUID, user: User) -> None:
    if owner_id != user.id:
        raise ForbiddenError("You can modify only your own resources")
