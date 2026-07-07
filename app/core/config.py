from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mini Social Network"
    environment: str = "local"
    database_url: str
    redis_url: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)
    verification_token_expire_hours: int = Field(default=24, ge=1)
    cleanup_unverified_after_hours: int = Field(default=48, ge=1)
    maintenance_token: SecretStr | None = None
    login_rate_limit_attempts: int = Field(default=5, ge=1)
    login_rate_limit_window_seconds: int = Field(default=15 * 60, ge=1)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    public_base_url: str = "http://localhost:8010"
    post_ttl_days: int | None = Field(default=None, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SOCIAL_",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "maintenance_token",
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "smtp_from_email",
        "post_ttl_days",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
