from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineDefinition, PipelineRun
from app.pipeline.executor import get_run_logs
from app.pipeline.validator import DagValidationError, validate_dag
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineResponse,
    PipelineRunResponse,
    PipelineUpdate,
    RunLogsResponse,
    RunTriggerResponse,
)
from app.services.audit_service import AuditService
from app.workers.tasks import run_pipeline_task


class PipelineNotFoundError(Exception):
    pass


class PipelineConflictError(Exception):
    pass


class PipelineValidationError(Exception):
    pass


class RunNotFoundError(Exception):
    pass


class PipelineService:
    def __init__(self) -> None:
        self._audit = AuditService()

    def _to_response(self, pipeline: PipelineDefinition) -> PipelineResponse:
        return PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            description=pipeline.description,
            dag_json=pipeline.dag_json,
            schedule_cron=pipeline.schedule_cron,
            is_active=pipeline.is_active,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
        )

    def _run_to_response(self, run: PipelineRun) -> PipelineRunResponse:
        return PipelineRunResponse(
            id=run.id,
            pipeline_id=run.pipeline_id,
            status=run.status,
            triggered_by=run.triggered_by,
            celery_task_id=run.celery_task_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            rows_read=run.rows_read,
            rows_written=run.rows_written,
            target_dataset_id=run.target_dataset_id,
            iceberg_snapshot_id=run.iceberg_snapshot_id,
            error_message=run.error_message,
            created_at=run.created_at,
        )

    async def list_pipelines(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[PipelineResponse], dict[str, Any]]:
        stmt = select(PipelineDefinition).where(PipelineDefinition.deleted_at.is_(None))
        count_stmt = (
            select(func.count())
            .select_from(PipelineDefinition)
            .where(PipelineDefinition.deleted_at.is_(None))
        )
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(PipelineDefinition.name.ilike(pattern))
            count_stmt = count_stmt.where(PipelineDefinition.name.ilike(pattern))

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = (
            stmt.order_by(PipelineDefinition.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        pipelines = (await db.execute(stmt)).scalars().all()
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
        return [self._to_response(p) for p in pipelines], meta

    async def get_pipeline(self, db: AsyncSession, pipeline_id: uuid.UUID) -> PipelineResponse:
        pipeline = await self._get_active(db, pipeline_id)
        return self._to_response(pipeline)

    async def create_pipeline(
        self,
        db: AsyncSession,
        body: PipelineCreate,
    ) -> PipelineResponse:
        if body.dag_json.get("nodes"):
            try:
                validate_dag(body.dag_json)
            except DagValidationError as exc:
                raise PipelineValidationError(str(exc)) from exc

        async with db.begin():
            pipeline = PipelineDefinition(
                name=body.name,
                description=body.description,
                dag_json=body.dag_json,
            )
            db.add(pipeline)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )
        return await self.get_pipeline(db, pipeline.id)

    async def update_pipeline(
        self,
        db: AsyncSession,
        pipeline_id: uuid.UUID,
        body: PipelineUpdate,
    ) -> PipelineResponse:
        if body.dag_json is not None:
            try:
                validate_dag(body.dag_json)
            except DagValidationError as exc:
                raise PipelineValidationError(str(exc)) from exc

        async with db.begin():
            pipeline = await self._get_active(db, pipeline_id)
            if body.name is not None:
                pipeline.name = body.name
            if body.description is not None:
                pipeline.description = body.description
            if body.dag_json is not None:
                pipeline.dag_json = body.dag_json
            if body.is_active is not None:
                pipeline.is_active = body.is_active
            pipeline.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )
        return await self.get_pipeline(db, pipeline_id)

    async def delete_pipeline(self, db: AsyncSession, pipeline_id: uuid.UUID) -> None:
        async with db.begin():
            pipeline = await self._get_active(db, pipeline_id)
            pipeline.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )

    async def trigger_run(
        self,
        db: AsyncSession,
        pipeline_id: uuid.UUID,
    ) -> RunTriggerResponse:
        pipeline = await self._get_active(db, pipeline_id)
        try:
            validate_dag(pipeline.dag_json)
        except DagValidationError as exc:
            raise PipelineValidationError(str(exc)) from exc

        async with db.begin():
            run = PipelineRun(
                pipeline_id=pipeline.id,
                status="queued",
                triggered_by="manual",
            )
            db.add(run)
            await db.flush()
            await self._audit.write(
                db,
                action="run",
                entity_type="pipeline_run",
                entity_id=run.id,
                payload={"pipeline_id": str(pipeline_id)},
            )

        task = run_pipeline_task.delay(str(run.id))
        async with db.begin():
            run_record = await db.get(PipelineRun, run.id)
            if run_record:
                run_record.celery_task_id = task.id

        return RunTriggerResponse(run_id=run.id, status="queued")

    async def get_run(self, db: AsyncSession, run_id: uuid.UUID) -> PipelineRunResponse:
        run = await db.get(PipelineRun, run_id)
        if run is None:
            raise RunNotFoundError("Pipeline run not found")
        return self._run_to_response(run)

    async def list_runs(
        self,
        db: AsyncSession,
        pipeline_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PipelineRunResponse], dict[str, Any]]:
        await self._get_active(db, pipeline_id)
        stmt = select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id)
        count_stmt = (
            select(func.count())
            .select_from(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
        )
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = (
            stmt.order_by(PipelineRun.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        runs = (await db.execute(stmt)).scalars().all()
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
        return [self._run_to_response(r) for r in runs], meta

    async def get_run_logs(self, run_id: uuid.UUID, since: int = 0) -> RunLogsResponse:
        lines, next_since = get_run_logs(run_id, since=since)
        return RunLogsResponse(lines=lines, next_since=next_since)

    async def _get_active(
        self,
        db: AsyncSession,
        pipeline_id: uuid.UUID,
    ) -> PipelineDefinition:
        pipeline = await db.get(PipelineDefinition, pipeline_id)
        if pipeline is None or pipeline.deleted_at is not None:
            raise PipelineNotFoundError("Pipeline not found")
        return pipeline
