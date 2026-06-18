from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.schemas.analytics import (
    DashboardCreate,
    DashboardUpdate,
    WidgetCreate,
    WidgetDataRequest,
    WidgetUpdate,
)
from app.services.analytics_service import (
    AnalyticsNotFoundError,
    AnalyticsService,
    AnalyticsValidationError,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _analytics_service() -> AnalyticsService:
    return AnalyticsService()


@router.get("/dashboards")
async def list_dashboards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    items, meta = await service.list_dashboards(db, page=page, page_size=page_size)
    return success([item.model_dump(mode="json") for item in items], meta=meta)


@router.post("/dashboards", status_code=201)
async def create_dashboard(
    body: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    dashboard = await service.create_dashboard(db, body)
    return success(dashboard.model_dump(mode="json"))


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        detail = await service.get_dashboard_detail(db, dashboard_id)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success({
        "dashboard": detail.dashboard.model_dump(mode="json"),
        "widgets": [w.model_dump(mode="json") for w in detail.widgets],
    })


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: uuid.UUID,
    body: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        dashboard = await service.update_dashboard(db, dashboard_id, body)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except AnalyticsValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(dashboard.model_dump(mode="json"))


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        await service.delete_dashboard(db, dashboard_id)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.post("/dashboards/{dashboard_id}/widgets", status_code=201)
async def create_widget(
    dashboard_id: uuid.UUID,
    body: WidgetCreate,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        widget = await service.create_widget(db, dashboard_id, body)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(widget.model_dump(mode="json"))


@router.put("/widgets/{widget_id}")
async def update_widget(
    widget_id: uuid.UUID,
    body: WidgetUpdate,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        widget = await service.update_widget(db, widget_id, body)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(widget.model_dump(mode="json"))


@router.delete("/widgets/{widget_id}")
async def delete_widget(
    widget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        await service.delete_widget(db, widget_id)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.post("/widgets/{widget_id}/data")
async def query_widget_data(
    widget_id: uuid.UUID,
    body: WidgetDataRequest,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_analytics_service),
):
    try:
        data = await service.query_widget_data(db, widget_id, body)
    except AnalyticsNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except AnalyticsValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(data.model_dump(mode="json"))
