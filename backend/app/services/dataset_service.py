from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.iceberg_catalog import get_catalog
from app.compute.duckdb_engine import DuckDBEngine
from app.connectors.base import get_connector
from app.models.dataset import Dataset
from app.models.source import DataSource
from app.schemas.dataset import (
    ColumnProfile,
    DatasetIngestRequest,
    DatasetResponse,
    DatasetUpdate,
    PreviewResponse,
    ProfileResponse,
)
from app.services.audit_service import AuditService
from app.services.lineage_service import LineageService
from app.services.source_service import SourceService, SourceValidationError


class DatasetNotFoundError(Exception):
    pass


class DatasetConflictError(Exception):
    pass


class DatasetValidationError(Exception):
    pass


class DatasetService:
    def __init__(self) -> None:
        self._audit = AuditService()
        self._lineage = LineageService()
        self._source_service = SourceService()

    def _to_response(self, dataset: Dataset) -> DatasetResponse:
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            display_name=dataset.display_name,
            description=dataset.description,
            source_id=dataset.source_id,
            iceberg_namespace=dataset.iceberg_namespace,
            iceberg_table=dataset.iceberg_table,
            iceberg_location=dataset.iceberg_location,
            schema_json=dataset.schema_json,
            row_count=dataset.row_count,
            size_bytes=dataset.size_bytes,
            last_synced_at=dataset.last_synced_at,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    async def list_datasets(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> tuple[list[DatasetResponse], dict[str, Any]]:
        stmt = select(Dataset).where(Dataset.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(Dataset).where(Dataset.deleted_at.is_(None))

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                Dataset.name.ilike(pattern) | Dataset.display_name.ilike(pattern)
            )
            count_stmt = count_stmt.where(
                Dataset.name.ilike(pattern) | Dataset.display_name.ilike(pattern)
            )
        if source_id:
            stmt = stmt.where(Dataset.source_id == source_id)
            count_stmt = count_stmt.where(Dataset.source_id == source_id)

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Dataset.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        datasets = (await db.execute(stmt)).scalars().all()

        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
        return [self._to_response(d) for d in datasets], meta

    async def get_dataset(self, db: AsyncSession, dataset_id: uuid.UUID) -> DatasetResponse:
        dataset = await self._get_active(db, dataset_id)
        return self._to_response(dataset)

    async def ingest(
        self,
        db: AsyncSession,
        request: DatasetIngestRequest,
    ) -> DatasetResponse:
        source = await db.get(DataSource, request.source_id)
        if source is None or source.deleted_at is not None:
            raise DatasetValidationError("Source not found or deleted")
        if not source.is_active:
            raise DatasetValidationError("Source is inactive")

        namespace = "default"
        table_name = request.dataset_name

        existing_stmt = select(Dataset).where(
            Dataset.iceberg_namespace == namespace,
            Dataset.iceberg_table == table_name,
            Dataset.deleted_at.is_(None),
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing and request.mode.value == "create":
            raise DatasetConflictError(f"Dataset '{table_name}' already exists")

        config = self._source_service._decrypt_config(source.config_encrypted)
        connector = get_connector(source.source_type, source.id, config)
        table = connector.read_table(request.table_or_file, limit=None)

        write_mode = "overwrite"

        engine = DuckDBEngine()
        try:
            snapshot_id = engine.write_iceberg(table, namespace, table_name, write_mode)
        finally:
            engine.close()

        catalog = get_catalog()
        iceberg_table = catalog.load_table(f"{namespace}.{table_name}")
        location = iceberg_table.location()

        schema_json = {
            "fields": [{"name": f.name, "type": str(f.type)} for f in table.schema]
        }
        now = datetime.now(timezone.utc)

        if existing:
            existing.display_name = request.display_name
            existing.source_id = request.source_id
            existing.iceberg_location = location
            existing.schema_json = schema_json
            existing.row_count = table.num_rows
            existing.last_synced_at = now
            existing.updated_at = now
            dataset = existing
        else:
            dataset = Dataset(
                name=table_name,
                display_name=request.display_name,
                source_id=request.source_id,
                iceberg_namespace=namespace,
                iceberg_table=table_name,
                iceberg_location=location,
                schema_json=schema_json,
                row_count=table.num_rows,
                last_synced_at=now,
            )
            db.add(dataset)

        await db.flush()
        await self._lineage.record_ingest(
            db,
            target_dataset_id=dataset.id,
            source_id=request.source_id,
            iceberg_snapshot_id=snapshot_id,
        )
        await self._audit.write(
            db,
            action="ingest",
            entity_type="dataset",
            entity_id=dataset.id,
            payload={"source_id": str(request.source_id), "table_or_file": request.table_or_file},
        )
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise DatasetConflictError(f"Dataset '{table_name}' already exists") from exc

        refreshed = await self._get_active(db, dataset.id)
        return self._to_response(refreshed)

    async def update_dataset(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
        body: DatasetUpdate,
    ) -> DatasetResponse:
        async with db.begin():
            dataset = await self._get_active(db, dataset_id)
            if body.display_name is not None:
                dataset.display_name = body.display_name
            if body.description is not None:
                dataset.description = body.description
            dataset.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="dataset",
                entity_id=dataset.id,
                payload=body.model_dump(exclude_unset=True),
            )
        return await self.get_dataset(db, dataset_id)

    async def delete_dataset(self, db: AsyncSession, dataset_id: uuid.UUID) -> None:
        async with db.begin():
            dataset = await self._get_active(db, dataset_id)
            dataset.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="dataset",
                entity_id=dataset.id,
            )

    async def preview(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
        limit: int = 100,
    ) -> PreviewResponse:
        dataset = await self._get_active(db, dataset_id)
        engine = DuckDBEngine()
        try:
            result = engine._conn.execute(
                f"SELECT * FROM iceberg_scan(?, allow_moved_paths=true) LIMIT {int(limit)}",
                [dataset.iceberg_location],
            ).fetch_arrow_table()
            count_result = engine._conn.execute(
                "SELECT COUNT(*) AS cnt FROM iceberg_scan(?, allow_moved_paths=true)",
                [dataset.iceberg_location],
            ).fetchone()
            total = int(count_result[0]) if count_result else 0
        finally:
            engine.close()

        columns = [f.name for f in result.schema]
        rows = [
            {col: _serialize_value(result[col][i].as_py()) for col in columns}
            for i in range(result.num_rows)
        ]
        return PreviewResponse(columns=columns, rows=rows, total=total)

    async def profile(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> ProfileResponse:
        dataset = await self._get_active(db, dataset_id)
        engine = DuckDBEngine()
        try:
            count_result = engine._conn.execute(
                "SELECT COUNT(*) FROM iceberg_scan(?, allow_moved_paths=true)",
                [dataset.iceberg_location],
            ).fetchone()
            row_count = int(count_result[0]) if count_result else 0

            schema_result = engine._conn.execute(
                "DESCRIBE SELECT * FROM iceberg_scan(?, allow_moved_paths=true)",
                [dataset.iceberg_location],
            ).fetchall()

            columns: list[ColumnProfile] = []
            for col_row in schema_result:
                col_name = col_row[0]
                col_type = col_row[1]
                stats = engine._conn.execute(
                    f"""
                    SELECT
                        COUNT(*) - COUNT({quote_ident(col_name)}) AS null_count,
                        COUNT({quote_ident(col_name)}) AS non_null_count,
                        approx_count_distinct({quote_ident(col_name)}) AS distinct_count,
                        MIN({quote_ident(col_name)}) AS min_value,
                        MAX({quote_ident(col_name)}) AS max_value
                    FROM iceberg_scan(?, allow_moved_paths=true)
                    """,
                    [dataset.iceberg_location],
                ).fetchone()
                columns.append(
                    ColumnProfile(
                        name=col_name,
                        type=col_type,
                        null_count=int(stats[0]) if stats else None,
                        non_null_count=int(stats[1]) if stats else None,
                        distinct_count=int(stats[2]) if stats else None,
                        min_value=_serialize_value(stats[3]) if stats else None,
                        max_value=_serialize_value(stats[4]) if stats else None,
                    )
                )
        finally:
            engine.close()

        return ProfileResponse(row_count=row_count, columns=columns)

    async def get_schema(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> dict[str, Any]:
        dataset = await self._get_active(db, dataset_id)
        return dataset.schema_json or {"fields": []}

    async def _get_active(self, db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None or dataset.deleted_at is not None:
            raise DatasetNotFoundError("Dataset not found")
        return dataset


def quote_ident(name: str) -> str:
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
