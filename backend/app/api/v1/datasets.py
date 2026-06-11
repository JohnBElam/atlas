from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.schemas.dataset import DatasetIngestRequest, DatasetUpdate
from app.services.dataset_service import (
    DatasetConflictError,
    DatasetNotFoundError,
    DatasetService,
    DatasetValidationError,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _dataset_service() -> DatasetService:
    return DatasetService()


@router.get("")
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    source_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    items, meta = await service.list_datasets(
        db, page=page, page_size=page_size, search=search, source_id=source_id
    )
    return success([item.model_dump(mode="json") for item in items], meta=meta)


@router.post("/ingest", status_code=201)
async def ingest_dataset(
    body: DatasetIngestRequest,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        dataset = await service.ingest(db, body)
    except DatasetValidationError as exc:
        return error_envelope(str(exc), 400)
    except DatasetConflictError as exc:
        return error_envelope(str(exc), 409)
    return success(dataset.model_dump(mode="json"))


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        dataset = await service.get_dataset(db, dataset_id)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(dataset.model_dump(mode="json"))


@router.put("/{dataset_id}")
async def update_dataset(
    dataset_id: uuid.UUID,
    body: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        dataset = await service.update_dataset(db, dataset_id, body)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(dataset.model_dump(mode="json"))


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        await service.delete_dataset(db, dataset_id)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        preview = await service.preview(db, dataset_id, limit=limit)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(preview.model_dump(mode="json"))


@router.get("/{dataset_id}/profile")
async def profile_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        profile = await service.profile(db, dataset_id)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(profile.model_dump(mode="json"))


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(_dataset_service),
):
    try:
        schema = await service.get_schema(db, dataset_id)
    except DatasetNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(schema)
