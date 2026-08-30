"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"

    # Google Cloud (optional for local)
    google_cloud_project: str = ""
    google_application_credentials: str = ""

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    environment: Literal["local", "development", "production"] = "local"

    # Database
    database_url: str = "sqlite:///./storage/reproducibility.db"

    # Storage
    storage_type: Literal["local", "gcs"] = "local"
    storage_path: str = "./storage"
    gcs_bucket: str = ""

    # Sandbox
    sandbox_type: Literal["docker"] = "docker"
    sandbox_timeout: int = 600  # 10 minutes
    sandbox_cpu_limit: float = 2.0
    sandbox_memory_limit: str = "4g"
    sandbox_network_enabled: bool = False

    # Retry
    max_retries: int = 3
    retry_delay: int = 5

    # Logging
    log_level: str = "INFO"

    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == "local"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


# Global settings instance
settings = Settings()
