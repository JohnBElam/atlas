from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    dag_json: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})


class PipelineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    dag_json: dict[str, Any] | None = None
    is_active: bool | None = None


class PipelineResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    dag_json: dict[str, Any]
    schedule_cron: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunTriggerResponse(BaseModel):
    run_id: UUID
    status: str


class PipelineRunResponse(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: str
    triggered_by: str
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    rows_read: int | None = None
    rows_written: int | None = None
    target_dataset_id: UUID | None = None
    iceberg_snapshot_id: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunLogsResponse(BaseModel):
    lines: list[str]
    next_since: int
