from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    CSV = "csv"
    PARQUET = "parquet"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    S3 = "s3"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REST_API = "rest_api"
    KAFKA = "kafka"


IMPLEMENTED_SOURCE_TYPES = {
    SourceType.CSV,
    SourceType.PARQUET,
    SourceType.POSTGRESQL,
}

STUB_SOURCE_TYPES = {
    SourceType.MYSQL,
    SourceType.S3,
    SourceType.SNOWFLAKE,
    SourceType.BIGQUERY,
    SourceType.REST_API,
    SourceType.KAFKA,
}


class ColumnDef(BaseModel):
    name: str
    type: str
    nullable: bool = True


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnDef]


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    config: dict[str, Any] = Field(default_factory=dict)


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: SourceType
    is_active: bool
    schema_cache: dict[str, Any] | None = None
    schema_discovered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestConnectionResponse(BaseModel):
    connected: bool


class SchemaDiscoveryResponse(BaseModel):
    tables: list[TableSchema]
    discovered_at: datetime | None = None


class UploadResponse(BaseModel):
    uploaded: bool
    filename: str
