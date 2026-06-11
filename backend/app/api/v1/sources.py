from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.schemas.source import SourceCreate, SourceUpdate
from app.services.source_service import (
    ConnectorNotImplementedError,
    SourceConflictError,
    SourceNotFoundError,
    SourceService,
    SourceValidationError,
)

router = APIRouter(prefix="/sources", tags=["sources"])


def _source_service() -> SourceService:
    return SourceService()


@router.get("")
async def list_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    items, meta = await service.list_sources(db, page=page, page_size=page_size, search=search)
    return success([item.model_dump(mode="json") for item in items], meta=meta)


@router.post("", status_code=201)
async def create_source(
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        source = await service.create_source(db, body)
    except SourceValidationError as exc:
        return error_envelope(str(exc), 400)
    except SourceConflictError as exc:
        return error_envelope(str(exc), 409)
    except IntegrityError as exc:
        return error_envelope("A source with this name already exists", 409)
    return success(source.model_dump(mode="json"))


@router.get("/{source_id}")
async def get_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        source = await service.get_source(db, source_id)
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(source.model_dump(mode="json"))


@router.put("/{source_id}")
async def update_source(
    source_id: uuid.UUID,
    body: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        source = await service.update_source(db, source_id, body)
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except SourceValidationError as exc:
        return error_envelope(str(exc), 400)
    except SourceConflictError as exc:
        return error_envelope(str(exc), 409)
    except IntegrityError as exc:
        return error_envelope("A source with this name already exists", 409)
    return success(source.model_dump(mode="json"))


@router.delete("/{source_id}")
async def delete_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        await service.delete_source(db, source_id)
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.post("/{source_id}/test")
async def test_source_connection(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        result = await service.test_connection(db, source_id)
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except ConnectorNotImplementedError as exc:
        return error_envelope(str(exc), 501)
    except SourceValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(result.model_dump(mode="json"))


@router.get("/{source_id}/schema")
async def get_source_schema(
    source_id: uuid.UUID,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    try:
        schema = await service.discover_schema(db, source_id, refresh=refresh)
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except ConnectorNotImplementedError as exc:
        return error_envelope(str(exc), 501)
    except SourceValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(schema.model_dump(mode="json"))


@router.post("/{source_id}/upload")
async def upload_source_file(
    source_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: SourceService = Depends(_source_service),
):
    content = await file.read()
    try:
        result = await service.upload_file(
            db,
            source_id,
            filename=file.filename or "upload",
            content=content,
        )
    except SourceNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except SourceValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(result.model_dump(mode="json"))
