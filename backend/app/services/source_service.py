from __future__ import annotations

import json
import math
import uuid
from datetime import UTC, datetime
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.connectors.base import get_connector
from app.models.source import DataSource
from app.schemas.source import (
    IMPLEMENTED_SOURCE_TYPES,
    ColumnDef,
    SchemaDiscoveryResponse,
    SourceCreate,
    SourceResponse,
    SourceType,
    SourceUpdate,
    TableSchema,
    TestConnectionResponse,
    UploadResponse,
)
from app.services.audit_service import AuditService
from app.storage.minio import get_minio_storage, sanitize_filename


class SourceNotFoundError(Exception):
    pass


class SourceConflictError(Exception):
    pass


class SourceValidationError(Exception):
    pass


class ConnectorNotImplementedError(Exception):
    pass


class SourceService:
    def __init__(self) -> None:
        self._audit = AuditService()
        self._fernet = Fernet(settings.fernet_key.encode())

    def _encrypt_config(self, config: dict[str, Any]) -> bytes:
        return self._fernet.encrypt(json.dumps(config).encode())

    def _decrypt_config(self, encrypted: bytes) -> dict[str, Any]:
        try:
            return json.loads(self._fernet.decrypt(encrypted).decode())
        except InvalidToken as exc:
            raise SourceValidationError("Stored source configuration is invalid") from exc

    def _to_response(self, source: DataSource) -> SourceResponse:
        return SourceResponse(
            id=source.id,
            name=source.name,
            source_type=SourceType(source.source_type),
            is_active=source.is_active,
            schema_cache=source.schema_cache,
            schema_discovered_at=source.schema_discovered_at,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    def _get_connector(self, source: DataSource):
        config = self._decrypt_config(source.config_encrypted)
        return get_connector(source.source_type, source.id, config)

    def _validate_config(self, source_type: SourceType, config: dict[str, Any]) -> None:
        if source_type == SourceType.POSTGRESQL and not config.get("connection_string"):
            raise SourceValidationError("PostgreSQL sources require connection_string in config")

    async def _get_active_source(self, db: AsyncSession, source_id: uuid.UUID) -> DataSource:
        result = await db.execute(
            select(DataSource).where(
                DataSource.id == source_id,
                DataSource.deleted_at.is_(None),
            )
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise SourceNotFoundError("Source not found")
        return source

    async def _commit_write(self, db: AsyncSession) -> None:
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise

    async def list_sources(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[SourceResponse], dict[str, Any]]:
        query = select(DataSource).where(DataSource.deleted_at.is_(None))
        count_query = select(func.count()).select_from(DataSource).where(
            DataSource.deleted_at.is_(None)
        )

        if search:
            pattern = f"%{search}%"
            query = query.where(DataSource.name.ilike(pattern))
            count_query = count_query.where(DataSource.name.ilike(pattern))

        total = (await db.execute(count_query)).scalar_one()
        total_pages = max(1, math.ceil(total / page_size)) if total else 0
        offset = (page - 1) * page_size

        result = await db.execute(
            query.order_by(DataSource.created_at.desc()).offset(offset).limit(page_size)
        )
        sources = result.scalars().all()
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
        return [self._to_response(source) for source in sources], meta

    async def create_source(self, db: AsyncSession, data: SourceCreate) -> SourceResponse:
        self._validate_config(data.source_type, data.config)
        source = DataSource(
            name=data.name,
            source_type=data.source_type.value,
            config_encrypted=self._encrypt_config(data.config),
        )
        db.add(source)
        try:
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="data_source",
                entity_id=source.id,
                payload={"name": source.name, "source_type": source.source_type},
            )
            await self._commit_write(db)
        except IntegrityError as exc:
            raise SourceConflictError("A source with this name already exists") from exc
        await db.refresh(source)
        return self._to_response(source)

    async def get_source(self, db: AsyncSession, source_id: uuid.UUID) -> SourceResponse:
        source = await self._get_active_source(db, source_id)
        return self._to_response(source)

    async def update_source(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
        data: SourceUpdate,
    ) -> SourceResponse:
        source = await self._get_active_source(db, source_id)
        changes: dict[str, Any] = {}

        if data.name is not None:
            changes["name"] = data.name
            source.name = data.name
        if data.config is not None:
            self._validate_config(SourceType(source.source_type), data.config)
            changes["config_updated"] = True
            source.config_encrypted = self._encrypt_config(data.config)
        if data.is_active is not None:
            changes["is_active"] = data.is_active
            source.is_active = data.is_active

        if not changes:
            return self._to_response(source)

        source.updated_at = datetime.now(UTC)
        try:
            await self._audit.write(
                db,
                action="update",
                entity_type="data_source",
                entity_id=source.id,
                payload=changes,
            )
            await self._commit_write(db)
        except IntegrityError as exc:
            raise SourceConflictError("A source with this name already exists") from exc
        await db.refresh(source)
        return self._to_response(source)

    async def delete_source(self, db: AsyncSession, source_id: uuid.UUID) -> None:
        source = await self._get_active_source(db, source_id)
        source.deleted_at = datetime.now(UTC)
        source.updated_at = datetime.now(UTC)
        await self._audit.write(
            db,
            action="soft_delete",
            entity_type="data_source",
            entity_id=source.id,
            payload={"name": source.name},
        )
        await self._commit_write(db)

    async def test_connection(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
    ) -> TestConnectionResponse:
        source = await self._get_active_source(db, source_id)
        if SourceType(source.source_type) not in IMPLEMENTED_SOURCE_TYPES:
            raise ConnectorNotImplementedError(
                f"{source.source_type} connector is not implemented in Phase 1"
            )
        connector = self._get_connector(source)
        try:
            connected = connector.test_connection()
        except NotImplementedError as exc:
            raise ConnectorNotImplementedError(str(exc)) from exc
        except Exception as exc:
            raise SourceValidationError("Connection test failed") from exc
        return TestConnectionResponse(connected=connected)

    async def discover_schema(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
        *,
        refresh: bool = False,
    ) -> SchemaDiscoveryResponse:
        source = await self._get_active_source(db, source_id)

        if not refresh and source.schema_cache:
            return SchemaDiscoveryResponse(
                tables=[TableSchema(**table) for table in source.schema_cache.get("tables", [])],
                discovered_at=source.schema_discovered_at,
            )

        if SourceType(source.source_type) not in IMPLEMENTED_SOURCE_TYPES:
            raise ConnectorNotImplementedError(
                f"{source.source_type} connector is not implemented in Phase 1"
            )

        connector = self._get_connector(source)
        try:
            table_names = connector.list_tables()
            tables: list[TableSchema] = []
            for table_name in table_names:
                columns = connector.get_schema(table_name)
                tables.append(
                    TableSchema(
                        name=table_name,
                        columns=[
                            ColumnDef(name=col.name, type=col.type, nullable=col.nullable)
                            for col in columns
                        ],
                    )
                )
        except NotImplementedError as exc:
            raise ConnectorNotImplementedError(str(exc)) from exc

        discovered_at = datetime.now(UTC)
        cache_payload = {
            "tables": [table.model_dump() for table in tables],
        }
        source.schema_cache = cache_payload
        source.schema_discovered_at = discovered_at
        source.updated_at = discovered_at

        await self._commit_write(db)
        await db.refresh(source)
        return SchemaDiscoveryResponse(tables=tables, discovered_at=discovered_at)

    async def upload_file(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
        *,
        filename: str,
        content: bytes,
    ) -> UploadResponse:
        source = await self._get_active_source(db, source_id)
        source_type = SourceType(source.source_type)
        if source_type not in {SourceType.CSV, SourceType.PARQUET}:
            raise SourceValidationError("Upload is only supported for CSV and Parquet sources")

        if not content:
            raise SourceValidationError("Empty files are not allowed")

        if len(content) > settings.max_upload_size_bytes:
            raise SourceValidationError(
                f"File exceeds maximum upload size of {settings.max_upload_size_bytes} bytes"
            )

        try:
            safe_filename = sanitize_filename(filename)
        except ValueError as exc:
            raise SourceValidationError(str(exc)) from exc

        storage = get_minio_storage()
        uploaded_name = storage.upload_file(source.id, safe_filename, content)
        source.updated_at = datetime.now(UTC)
        await self._commit_write(db)
        await db.refresh(source)
        return UploadResponse(uploaded=True, filename=uploaded_name)
