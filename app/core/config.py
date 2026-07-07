from functools import lru_cache

from pydantic import Field, SecretStr
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SOCIAL_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
