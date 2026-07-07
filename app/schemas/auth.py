from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.users import USERNAME_PATTERN, UserRead


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided")
        if self.email and self.username:
            raise ValueError("Use either email or username, not both")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105


class RegisterResponse(BaseModel):
    user: UserRead
    verification_token: str
