"""Configuration for standalone Agent Service V2."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8092

    # Database: PostgreSQL Server 184 (Strict Read-Only)
    ESP_APM_DB_URL: str = "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db"
    ESP_APM_READONLY: bool = True

    # LLM Gateway
    AI_ENABLED: bool = True
    LLM_API_BASE: str = "http://192.168.1.188:8080/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_MODEL: str = "Qwen2.5-Coder-3B-Instruct-Q4_K_M"
    LLM_TIMEOUT: int = 60

    @property
    def ai_actually_enabled(self) -> bool:
        return self.AI_ENABLED and bool(self.LLM_API_BASE)


settings = Settings()
