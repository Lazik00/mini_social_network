from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.users import UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def update_current_user(self, user: User, data: UserUpdate) -> User:
        if data.username and data.username != user.username:
            existing_user = await self.users.get_by_username(data.username)
            if existing_user:
                raise ConflictError("User with this username already exists")

        try:
            updated_user = await self.users.update_profile(
                user,
                username=data.username,
                full_name=data.full_name,
            )
            await self.session.commit()
            return updated_user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("User with this username already exists") from exc
