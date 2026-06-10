from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(alias="DATABASE_URL")
    celery_database_url: str = Field(alias="CELERY_DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket_data: str = Field(alias="MINIO_BUCKET_DATA")
    minio_bucket_iceberg: str = Field(alias="MINIO_BUCKET_ICEBERG")
    s3_use_ssl: bool = Field(default=False, alias="S3_USE_SSL")

    iceberg_warehouse: str = Field(alias="ICEBERG_WAREHOUSE")
    iceberg_catalog_uri: str = Field(alias="ICEBERG_CATALOG_URI")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")

    fernet_key: str = Field(alias="FERNET_KEY")
    max_upload_size_bytes: int = Field(
        default=500 * 1024 * 1024,
        alias="MAX_UPLOAD_SIZE_BYTES",
    )

    @property
    def s3_endpoint_url(self) -> str:
        scheme = "https" if self.s3_use_ssl else "http"
        return f"{scheme}://{self.minio_endpoint}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
