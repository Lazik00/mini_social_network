from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,32}$"
FULL_NAME_PATTERN = r"^[A-Za-zА-Яа-яЁё\s-]+$"


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)
    full_name: str = Field(min_length=2, max_length=100, pattern=FULL_NAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=USERNAME_PATTERN,
    )
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        pattern=FULL_NAME_PATTERN,
    )

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UserUpdate":
        if self.username is None and self.full_name is None:
            raise ValueError("At least one of username or full_name must be provided")
        return self
