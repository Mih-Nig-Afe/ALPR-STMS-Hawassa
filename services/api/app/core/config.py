from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(alias="APP_ENV")
    app_debug: bool = Field(alias="APP_DEBUG")
    app_name: str = Field(alias="APP_NAME")
    app_public_url: str = Field(alias="APP_PUBLIC_URL")
    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    app_http_port: int = Field(alias="APP_HTTP_PORT")
    session_cookie_name: str = Field(alias="SESSION_COOKIE_NAME")
    session_ttl_hours: int = Field(alias="SESSION_TTL_HOURS")
    default_timezone: str = Field(alias="DEFAULT_TIMEZONE")

    database_url: str = Field(alias="DATABASE_URL")
    worker_database_url: str = Field(alias="WORKER_DATABASE_URL")
    alembic_database_url: str = Field(alias="ALEMBIC_DATABASE_URL")
    postgrest_database_url: str = Field(alias="POSTGREST_DATABASE_URL")
    storage_database_url: str = Field(alias="STORAGE_DATABASE_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_expiry: int = Field(alias="JWT_EXPIRY")
    anon_key: str = Field(alias="ANON_KEY")
    service_role_key: str = Field(alias="SERVICE_ROLE_KEY")

    storage_bucket: str = Field(alias="STORAGE_BUCKET")
    storage_tenant_id: str = Field(alias="STORAGE_TENANT_ID")
    storage_public_url: str = Field(alias="STORAGE_PUBLIC_URL")
    file_storage_backend_path: str = Field(alias="FILE_STORAGE_BACKEND_PATH")
    global_s3_bucket: str = Field(alias="GLOBAL_S3_BUCKET")
    region: str = Field(alias="REGION")

    payment_callback_shared_secret: str = Field(alias="PAYMENT_CALLBACK_SHARED_SECRET")
    payment_provider_mode: str = Field(alias="PAYMENT_PROVIDER_MODE")

    smtp_host: str = Field(alias="SMTP_HOST")
    smtp_port: int = Field(alias="SMTP_PORT")
    smtp_user: str = Field(alias="SMTP_USER", default="")
    smtp_pass: str = Field(alias="SMTP_PASS", default="")
    smtp_from: str = Field(alias="SMTP_FROM")

    map_tile_url: str = Field(alias="MAP_TILE_URL")
    map_tile_attribution: str = Field(alias="MAP_TILE_ATTRIBUTION")

    worker_poll_seconds: int = Field(alias="WORKER_POLL_SECONDS")
    worker_batch_size: int = Field(alias="WORKER_BATCH_SIZE")
    officer_default_password: str = Field(alias="OFFICER_DEFAULT_PASSWORD")
    admin_default_password: str = Field(alias="ADMIN_DEFAULT_PASSWORD")
    complaint_default_password: str = Field(alias="COMPLAINT_DEFAULT_PASSWORD")
    subcity_default_password: str = Field(alias="SUBCITY_DEFAULT_PASSWORD")

    storage_internal_url: str = "http://supabase-storage:5000"

    @property
    def secure_cookies(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

