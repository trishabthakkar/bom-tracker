from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_JWT_SECRET = "change-this-dev-secret-before-production"


class Settings(BaseSettings):
    app_name: str = "AI-Assisted BOM Change Intelligence Layer"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://bom_tracker:bom_tracker_password@localhost:5432/bom_tracker"
    )
    backend_cors_origins: str = Field(
        default=(
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:5174,"
            "http://127.0.0.1:5174"
        )
    )
    jwt_secret_key: str = DEFAULT_DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    upload_directory: str = "uploads"
    max_upload_size_mb: int = 25
    llm_provider: str = "rule_based"
    auth_rate_limit_per_minute: int = 10
    mutation_rate_limit_per_minute: int = 120
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = 20
    llm_fallback_to_rule_based: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def secure_cookies(self) -> bool:
        return self.environment.lower() in {"production", "staging"}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if (
            self.environment.lower() == "production"
            and self.jwt_secret_key == DEFAULT_DEV_JWT_SECRET
        ):
            raise ValueError("JWT_SECRET_KEY must be changed in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
