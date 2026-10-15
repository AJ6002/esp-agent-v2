"""Application settings: injected via environment variables with secure defaults."""

from __future__ import annotations

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-this-to-a-random-secret-key-in-production"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "Industrial Maintenance Copilot"
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Database: empty defaults to SQLite for zero-config local startup
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    AUTO_MIGRATE_ON_STARTUP: bool | None = None

    # ESP APM PostgreSQL (Server 184) - Strict Read-Only
    ESP_APM_DB_URL: str = "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db"
    ESP_APM_READONLY: bool = True

    # Authentication
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    AI_ENABLED: bool = True
    LLM_API_BASE: str = "http://192.168.1.188:8080/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_MODEL: str = "Qwen2.5-Coder-3B-Instruct-Q4_K_M"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    AI_REQUEST_TIMEOUT_SECONDS: int = 60

    # Transition high-risk commands exceeding timeout to manual verification.
    EQUIPMENT_COMMAND_TIMEOUT_SECONDS: int = Field(default=300, ge=30, le=3600)

    # Industrial protocol gateway (OPC UA, read-only). Disabled by default.
    GATEWAY_ENABLED: bool = False
    GATEWAY_MODE: str = "mock"  # mock: in-process client; opcua: physical OPC UA connection
    GATEWAY_ENDPOINT: str = ""  # Empty uses mode default endpoint
    GATEWAY_POLL_INTERVAL_SECONDS: float = Field(default=5.0, ge=1.0)
    GATEWAY_AUTO_INGEST: bool = True
    GATEWAY_MAPPING_CONFIG: str = "configs/opcua-node-mapping.yaml"
    GATEWAY_TIMEOUT_SECONDS: float = Field(default=4.0, ge=1.0)

    # OPC UA DataChange subscription (event-driven, read-only). Disabled by default.
    GATEWAY_SUBSCRIPTION_ENABLED: bool = False
    GATEWAY_SUBSCRIPTION_SAMPLING_MS: float = Field(default=1000.0, ge=100.0)
    GATEWAY_SUBSCRIPTION_DEBOUNCE_MS: float = Field(default=1000.0, ge=100.0)

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_DIR: str = "./uploads"
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = ""

    # Demo data
    SEED_ON_STARTUP: bool = True

    # Observability (Optional OpenTelemetry; runs smoothly without Collector)
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "industrial-maintenance-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    # Sample rate 0.0~1.0; 1.0 recommended for local/demo.
    OTEL_TRACE_SAMPLE_RATE: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.strip().lower() == "development"

    @model_validator(mode="after")
    def reject_unsafe_non_development_config(self) -> Settings:
        if self.is_development:
            return self

        secret_key = self.SECRET_KEY.strip()
        if secret_key == DEFAULT_SECRET_KEY or len(secret_key) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"Non-development environment must configure random SECRET_KEY of at least {MIN_SECRET_KEY_LENGTH} characters"
            )
        if self.SEED_ON_STARTUP:
            raise ValueError("SEED_ON_STARTUP is prohibited in non-development environments")
        if self.AUTO_MIGRATE_ON_STARTUP:
            raise ValueError("Automatic database migrations on application startup are prohibited in non-development environments")
        return self

    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace(
                    "postgres://", "postgresql+psycopg://", 1
                )
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+psycopg://", 1
                )
            return self.DATABASE_URL
        # SQLite default file database
        return "sqlite:///./maintenance.db"

    @property
    def auto_migrate_on_startup(self) -> bool:
        if self.AUTO_MIGRATE_ON_STARTUP is not None:
            return self.AUTO_MIGRATE_ON_STARTUP
        return self.is_development

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.FRONTEND_URL]
        # Allow common local ports in development environment
        if self.is_development:
            origins.extend(
                [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:3001",
                ]
            )
        # Deduplicate
        return list(dict.fromkeys(origins))

    @property
    def ai_actually_enabled(self) -> bool:
        """AI operational flag: enabled and API Key configured."""
        return bool(self.AI_ENABLED and self.LLM_API_KEY and self.LLM_MODEL)


settings = Settings()
