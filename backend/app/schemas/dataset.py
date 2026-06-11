from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class IngestMode(str, Enum):
    CREATE = "create"
    OVERWRITE = "overwrite"


class DatasetIngestRequest(BaseModel):
    source_id: UUID
    table_or_file: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    mode: IngestMode = IngestMode.CREATE


class DatasetUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    source_id: UUID | None = None
    iceberg_namespace: str
    iceberg_table: str
    iceberg_location: str
    schema_json: dict[str, Any] | None = None
    row_count: int | None = None
    size_bytes: int | None = None
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int


class ColumnProfile(BaseModel):
    name: str
    type: str
    distinct_count: int | None = None
    null_count: int | None = None
    non_null_count: int | None = None
    min_value: Any | None = None
    max_value: Any | None = None


class ProfileResponse(BaseModel):
    row_count: int
    columns: list[ColumnProfile]
