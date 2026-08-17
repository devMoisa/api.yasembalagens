from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YAS_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Yas Embalagens API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./yas.sqlite3"
    secret_key: str = "development-only-change-me-use-at-least-32-bytes"
    access_token_expire_minutes: int = 480
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    max_upload_size_mb: int = 5

    spaces_region: str = "nyc3"
    spaces_bucket: str = ""
    spaces_access_key: str = ""
    spaces_secret_key: str = ""
    spaces_endpoint_url: str = ""
    spaces_cdn_url: str = ""
    spaces_key_prefix: str = "media"

    @field_validator("secret_key")
    @classmethod
    def reject_default_secret_in_production(cls, value: str, info) -> str:
        environment = info.data.get("environment", "development")
        is_default = value == "development-only-change-me-use-at-least-32-bytes"
        if environment == "production" and is_default:
            raise ValueError("YAS_SECRET_KEY deve ser configurada em producao")
        return value

    @property
    def resolved_spaces_endpoint(self) -> str:
        return self.spaces_endpoint_url or f"https://{self.spaces_region}.digitaloceanspaces.com"

    @property
    def resolved_spaces_public_base(self) -> str:
        if self.spaces_cdn_url:
            return self.spaces_cdn_url.rstrip("/")
        return f"https://{self.spaces_bucket}.{self.spaces_region}.cdn.digitaloceanspaces.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
