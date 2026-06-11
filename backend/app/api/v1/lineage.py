from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.services.lineage_service import LineageNotFoundError, LineageService

router = APIRouter(prefix="/lineage", tags=["lineage"])


def _lineage_service() -> LineageService:
    return LineageService()


@router.get("/graph")
async def get_lineage_graph(
    db: AsyncSession = Depends(get_db),
    service: LineageService = Depends(_lineage_service),
):
    graph = await service.get_full_graph(db)
    return success(graph.model_dump(mode="json"))


@router.get("/dataset/{dataset_id}")
async def get_dataset_lineage(
    dataset_id: uuid.UUID,
    hops: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    service: LineageService = Depends(_lineage_service),
):
    try:
        graph = await service.get_dataset_subgraph(db, dataset_id, hops=hops)
    except LineageNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(graph.model_dump(mode="json"))


@router.get("/dataset/{dataset_id}/snapshots")
async def get_dataset_snapshots(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: LineageService = Depends(_lineage_service),
):
    try:
        snapshots = await service.get_snapshot_history(db, dataset_id)
    except LineageNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success([s.model_dump(mode="json") for s in snapshots])
