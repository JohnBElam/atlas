from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.schemas.pipeline import PipelineCreate, PipelineUpdate
from app.services.pipeline_service import (
    PipelineNotFoundError,
    PipelineService,
    PipelineValidationError,
    RunNotFoundError,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _pipeline_service() -> PipelineService:
    return PipelineService()


@router.get("")
async def list_pipelines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    items, meta = await service.list_pipelines(
        db, page=page, page_size=page_size, search=search
    )
    return success([item.model_dump(mode="json") for item in items], meta=meta)


@router.post("", status_code=201)
async def create_pipeline(
    body: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        pipeline = await service.create_pipeline(db, body)
    except PipelineValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(pipeline.model_dump(mode="json"))


@router.get("/runs/{run_id}")
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        run = await service.get_run(db, run_id)
    except RunNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(run.model_dump(mode="json"))


@router.get("/runs/{run_id}/logs")
async def get_run_logs(
    run_id: uuid.UUID,
    since: int = Query(0, ge=0),
    service: PipelineService = Depends(_pipeline_service),
):
    logs = await service.get_run_logs(run_id, since=since)
    return success(logs.model_dump(mode="json"))


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        pipeline = await service.get_pipeline(db, pipeline_id)
    except PipelineNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(pipeline.model_dump(mode="json"))


@router.put("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: uuid.UUID,
    body: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        pipeline = await service.update_pipeline(db, pipeline_id, body)
    except PipelineNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except PipelineValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(pipeline.model_dump(mode="json"))


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        await service.delete_pipeline(db, pipeline_id)
    except PipelineNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.post("/{pipeline_id}/run", status_code=201)
async def run_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        result = await service.trigger_run(db, pipeline_id)
    except PipelineNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except PipelineValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(result.model_dump(mode="json"))


@router.get("/{pipeline_id}/runs")
async def list_pipeline_runs(
    pipeline_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
):
    try:
        items, meta = await service.list_runs(
            db, pipeline_id, page=page, page_size=page_size
        )
    except PipelineNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success([item.model_dump(mode="json") for item in items], meta=meta)
