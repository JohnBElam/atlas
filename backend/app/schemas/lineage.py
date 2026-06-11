from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LineageNodeData(BaseModel):
    id: str
    label: str
    node_type: str
    entity_id: UUID
    row_count: int | None = None
    connector_type: str | None = None
    last_run_status: str | None = None
    last_updated: datetime | None = None
    extra: dict[str, Any] | None = None


class LineageGraphNode(BaseModel):
    id: str
    type: str = "default"
    position: dict[str, float]
    data: LineageNodeData


class LineageGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class LineageGraphResponse(BaseModel):
    nodes: list[LineageGraphNode]
    edges: list[LineageGraphEdge]


class SnapshotHistoryItem(BaseModel):
    snapshot_id: int
    committed_at: datetime | None = None
    operation: str | None = None
    summary: str | None = None
