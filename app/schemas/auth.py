from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.users import USERNAME_PATTERN, UserRead


class LoginRequest(BaseModel):
    email: EmailStr | None = Field(
        default=None,
        description="Use either email or username, not both.",
    )
    username: str | None = Field(
        default=None,
        pattern=USERNAME_PATTERN,
        description="Use either username or email, not both.",
    )
    password: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "lazizyunusov@gmail.com",
                    "password": "Laziz123",
                },
                {
                    "username": "lazizyunusov",
                    "password": "Laziz123",
                },
            ]
        }
    )

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided")
        if self.email and self.username:
            raise ValueError("Use either email or username, not both")
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    user: UserRead
    verification_token: str
