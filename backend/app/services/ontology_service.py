from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.compute.duckdb_engine import DuckDBEngine
from app.models.dataset import Dataset
from app.models.ontology import LinkType, ObjectProperty, ObjectType
from app.schemas.ontology import (
    LinkTypeCreate,
    LinkTypeResponse,
    LinkTypeUpdate,
    ObjectListResponse,
    ObjectPropertyCreate,
    ObjectPropertyResponse,
    ObjectPropertyUpdate,
    ObjectTypeCreate,
    ObjectTypeResponse,
    ObjectTypeUpdate,
    OntologyGraphEdge,
    OntologyGraphNode,
    OntologyGraphResponse,
)
from app.services.audit_service import AuditService
from app.services.dataset_service import quote_ident


class OntologyNotFoundError(Exception):
    pass


class OntologyConflictError(Exception):
    pass


class OntologyValidationError(Exception):
    pass


class OntologyService:
    def __init__(self) -> None:
        self._audit = AuditService()

    def _type_to_response(self, obj_type: ObjectType) -> ObjectTypeResponse:
        return ObjectTypeResponse(
            id=obj_type.id,
            name=obj_type.name,
            display_name=obj_type.display_name,
            description=obj_type.description,
            icon=obj_type.icon,
            color=obj_type.color,
            primary_key_property_id=obj_type.primary_key_property_id,
            created_at=obj_type.created_at,
            updated_at=obj_type.updated_at,
        )

    def _property_to_response(self, prop: ObjectProperty) -> ObjectPropertyResponse:
        return ObjectPropertyResponse(
            id=prop.id,
            object_type_id=prop.object_type_id,
            name=prop.name,
            display_name=prop.display_name,
            data_type=prop.data_type,
            is_required=prop.is_required,
            dataset_id=prop.dataset_id,
            column_name=prop.column_name,
            description=prop.description,
            sort_order=prop.sort_order,
            created_at=prop.created_at,
            updated_at=prop.updated_at,
        )

    def _link_to_response(self, link: LinkType) -> LinkTypeResponse:
        return LinkTypeResponse(
            id=link.id,
            name=link.name,
            display_name=link.display_name,
            from_object_type_id=link.from_object_type_id,
            to_object_type_id=link.to_object_type_id,
            cardinality=link.cardinality,
            from_property_id=link.from_property_id,
            to_property_id=link.to_property_id,
            description=link.description,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

    async def list_types(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ObjectTypeResponse], dict[str, Any]]:
        stmt = select(ObjectType).where(ObjectType.deleted_at.is_(None))
        count_stmt = (
            select(func.count()).select_from(ObjectType).where(ObjectType.deleted_at.is_(None))
        )
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = (
            stmt.order_by(ObjectType.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        types = (await db.execute(stmt)).scalars().all()
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
        return [self._type_to_response(t) for t in types], meta

    async def get_type(self, db: AsyncSession, type_id: uuid.UUID) -> ObjectTypeResponse:
        obj_type = await self._get_active_type(db, type_id)
        return self._type_to_response(obj_type)

    async def create_type(
        self,
        db: AsyncSession,
        body: ObjectTypeCreate,
    ) -> ObjectTypeResponse:
        async with db.begin():
            obj_type = ObjectType(
                name=body.name,
                display_name=body.display_name,
                description=body.description,
                icon=body.icon,
                color=body.color,
            )
            db.add(obj_type)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="object_type",
                entity_id=obj_type.id,
            )
        return await self.get_type(db, obj_type.id)

    async def update_type(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
        body: ObjectTypeUpdate,
    ) -> ObjectTypeResponse:
        async with db.begin():
            obj_type = await self._get_active_type(db, type_id)
            if body.display_name is not None:
                obj_type.display_name = body.display_name
            if body.description is not None:
                obj_type.description = body.description
            if body.icon is not None:
                obj_type.icon = body.icon
            if body.color is not None:
                obj_type.color = body.color
            if body.primary_key_property_id is not None:
                prop = await db.get(ObjectProperty, body.primary_key_property_id)
                if prop is None or prop.deleted_at is not None or prop.object_type_id != type_id:
                    raise OntologyValidationError("Invalid primary key property")
                obj_type.primary_key_property_id = body.primary_key_property_id
            obj_type.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="object_type",
                entity_id=obj_type.id,
            )
        return await self.get_type(db, type_id)

    async def delete_type(self, db: AsyncSession, type_id: uuid.UUID) -> None:
        async with db.begin():
            obj_type = await self._get_active_type(db, type_id)
            obj_type.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="object_type",
                entity_id=obj_type.id,
            )

    async def create_property(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
        body: ObjectPropertyCreate,
    ) -> ObjectPropertyResponse:
        await self._get_active_type(db, type_id)
        async with db.begin():
            prop = ObjectProperty(
                object_type_id=type_id,
                name=body.name,
                display_name=body.display_name,
                data_type=body.data_type.value,
                is_required=body.is_required,
                dataset_id=body.dataset_id,
                column_name=body.column_name,
                description=body.description,
                sort_order=body.sort_order,
            )
            db.add(prop)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="object_property",
                entity_id=prop.id,
            )
        return self._property_to_response(prop)

    async def get_property(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
    ) -> ObjectPropertyResponse:
        prop = await self._get_active_property(db, property_id)
        return self._property_to_response(prop)

    async def update_property(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        body: ObjectPropertyUpdate,
    ) -> ObjectPropertyResponse:
        async with db.begin():
            prop = await self._get_active_property(db, property_id)
            if body.display_name is not None:
                prop.display_name = body.display_name
            if body.data_type is not None:
                prop.data_type = body.data_type.value
            if body.is_required is not None:
                prop.is_required = body.is_required
            if body.dataset_id is not None:
                prop.dataset_id = body.dataset_id
            if body.column_name is not None:
                prop.column_name = body.column_name
            if body.description is not None:
                prop.description = body.description
            if body.sort_order is not None:
                prop.sort_order = body.sort_order
            prop.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="object_property",
                entity_id=prop.id,
            )
        refreshed = await self._get_active_property(db, property_id)
        return self._property_to_response(refreshed)

    async def delete_property(self, db: AsyncSession, property_id: uuid.UUID) -> None:
        async with db.begin():
            prop = await self._get_active_property(db, property_id)
            prop.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="object_property",
                entity_id=prop.id,
            )

    async def list_properties_for_type(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
    ) -> list[ObjectPropertyResponse]:
        await self._get_active_type(db, type_id)
        stmt = (
            select(ObjectProperty)
            .where(
                ObjectProperty.object_type_id == type_id,
                ObjectProperty.deleted_at.is_(None),
            )
            .order_by(ObjectProperty.sort_order)
        )
        props = (await db.execute(stmt)).scalars().all()
        return [self._property_to_response(p) for p in props]

    async def list_links(self, db: AsyncSession) -> list[LinkTypeResponse]:
        stmt = select(LinkType).where(LinkType.deleted_at.is_(None))
        links = (await db.execute(stmt)).scalars().all()
        return [self._link_to_response(link) for link in links]

    async def create_link(self, db: AsyncSession, body: LinkTypeCreate) -> LinkTypeResponse:
        async with db.begin():
            link = LinkType(
                name=body.name,
                display_name=body.display_name,
                from_object_type_id=body.from_object_type_id,
                to_object_type_id=body.to_object_type_id,
                cardinality=body.cardinality.value,
                from_property_id=body.from_property_id,
                to_property_id=body.to_property_id,
                description=body.description,
            )
            db.add(link)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="link_type",
                entity_id=link.id,
            )
        return self._link_to_response(link)

    async def update_link(
        self,
        db: AsyncSession,
        link_id: uuid.UUID,
        body: LinkTypeUpdate,
    ) -> LinkTypeResponse:
        async with db.begin():
            link = await self._get_active_link(db, link_id)
            if body.display_name is not None:
                link.display_name = body.display_name
            if body.description is not None:
                link.description = body.description
            link.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="link_type",
                entity_id=link.id,
            )
        refreshed = await self._get_active_link(db, link_id)
        return self._link_to_response(refreshed)

    async def delete_link(self, db: AsyncSession, link_id: uuid.UUID) -> None:
        async with db.begin():
            link = await self._get_active_link(db, link_id)
            link.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="link_type",
                entity_id=link.id,
            )

    async def get_graph(self, db: AsyncSession) -> OntologyGraphResponse:
        types_stmt = select(ObjectType).where(ObjectType.deleted_at.is_(None))
        types = (await db.execute(types_stmt)).scalars().all()
        links_stmt = select(LinkType).where(LinkType.deleted_at.is_(None))
        links = (await db.execute(links_stmt)).scalars().all()

        nodes: list[OntologyGraphNode] = []
        for i, obj_type in enumerate(types):
            nodes.append(
                OntologyGraphNode(
                    id=str(obj_type.id),
                    position={"x": (i % 4) * 250, "y": (i // 4) * 150},
                    data={
                        "label": obj_type.display_name,
                        "name": obj_type.name,
                        "icon": obj_type.icon,
                        "color": obj_type.color,
                    },
                )
            )

        edges: list[OntologyGraphEdge] = []
        for link in links:
            edges.append(
                OntologyGraphEdge(
                    id=str(link.id),
                    source=str(link.from_object_type_id),
                    target=str(link.to_object_type_id),
                    label=link.display_name,
                )
            )
        return OntologyGraphResponse(nodes=nodes, edges=edges)

    async def list_objects(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[ObjectListResponse, dict[str, Any]]:
        obj_type = await self._get_active_type(db, type_id)
        if not obj_type.primary_key_property_id:
            raise OntologyValidationError("Primary key property must be set before browsing objects")

        props_stmt = select(ObjectProperty).where(
            ObjectProperty.object_type_id == type_id,
            ObjectProperty.deleted_at.is_(None),
        )
        properties = (await db.execute(props_stmt)).scalars().all()
        if not properties:
            raise OntologyValidationError("Object type has no properties")

        pk_prop = next((p for p in properties if p.id == obj_type.primary_key_property_id), None)
        if pk_prop is None:
            raise OntologyValidationError("Primary key property not found")

        unmapped = [p for p in properties if not p.dataset_id or not p.column_name]
        if unmapped:
            raise OntologyValidationError(
                f"All properties must be mapped to dataset columns: {[p.name for p in unmapped]}"
            )

        dataset_groups: dict[uuid.UUID, list[ObjectProperty]] = {}
        for prop in properties:
            dataset_groups.setdefault(prop.dataset_id, []).append(prop)

        for ds_id, ds_props in dataset_groups.items():
            pk_in_dataset = any(p.id == pk_prop.id and p.dataset_id == ds_id for p in ds_props)
            if not pk_in_dataset:
                pk_col = pk_prop.column_name
                has_pk = any(p.column_name == pk_col and p.dataset_id == ds_id for p in ds_props)
                if not has_pk:
                    raise OntologyValidationError(
                        f"Dataset {ds_id} must map the primary key column '{pk_col}'"
                    )

        sql, params = await self._build_object_query(
            db, properties, pk_prop, dataset_groups, search
        )
        offset = (page - 1) * page_size

        engine = DuckDBEngine()
        try:
            count_sql = f"SELECT COUNT(*) FROM ({sql}) AS obj_q"
            total = int(engine._conn.execute(count_sql, params).fetchone()[0])

            paged_sql = f"{sql} LIMIT {int(page_size)} OFFSET {int(offset)}"
            result = engine._conn.execute(paged_sql, params).fetch_arrow_table()
        finally:
            engine.close()

        columns = [p.name for p in sorted(properties, key=lambda x: x.sort_order)]
        rows = []
        col_names = [f.name for f in result.schema]
        for i in range(result.num_rows):
            row = {col: result[col][i].as_py() for col in col_names if col in columns}
            rows.append(row)

        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if page_size else 1,
        }
        return ObjectListResponse(columns=columns, rows=rows), meta

    async def get_object(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
        pk_value: str,
    ) -> dict[str, Any]:
        objects, _ = await self.list_objects(db, type_id, page=1, page_size=1000)
        for row in objects.rows:
            for val in row.values():
                if str(val) == pk_value:
                    return row
        raise OntologyNotFoundError("Object not found")

    async def traverse_link(
        self,
        db: AsyncSession,
        type_id: uuid.UUID,
        pk_value: str,
        link_type_id: uuid.UUID,
    ) -> ObjectListResponse:
        link = await self._get_active_link(db, link_type_id)
        from_prop = await self._get_active_property(db, link.from_property_id)
        to_prop = await self._get_active_property(db, link.to_property_id)

        if not from_prop.dataset_id or not to_prop.dataset_id:
            raise OntologyValidationError("Link properties must be mapped to datasets")

        from_ds = await db.get(Dataset, from_prop.dataset_id)
        to_ds = await db.get(Dataset, to_prop.dataset_id)
        if not from_ds or not to_ds:
            raise OntologyValidationError("Mapped datasets not found")

        engine = DuckDBEngine()
        try:
            sql = f"""
            SELECT to_tbl.*
            FROM iceberg_scan(?, allow_moved_paths=true) AS from_tbl
            JOIN iceberg_scan(?, allow_moved_paths=true) AS to_tbl
              ON from_tbl.{quote_ident(from_prop.column_name)} = to_tbl.{quote_ident(to_prop.column_name)}
            WHERE CAST(from_tbl.{quote_ident(from_prop.column_name)} AS VARCHAR) = ?
            """
            result = engine._conn.execute(
                sql,
                [from_ds.iceberg_location, to_ds.iceberg_location, pk_value],
            ).fetch_arrow_table()
        finally:
            engine.close()

        columns = [f.name for f in result.schema]
        rows = [
            {col: result[col][i].as_py() for col in columns}
            for i in range(result.num_rows)
        ]
        return ObjectListResponse(columns=columns, rows=rows)

    async def _build_object_query(
        self,
        db: AsyncSession,
        properties: list[ObjectProperty],
        pk_prop: ObjectProperty,
        dataset_groups: dict[uuid.UUID, list[ObjectProperty]],
        search: str | None,
    ) -> tuple[str, list[Any]]:
        params: list[Any] = []
        ds_ids = list(dataset_groups.keys())

        if len(ds_ids) == 1:
            ds_id = ds_ids[0]
            ds_props = dataset_groups[ds_id]
            select_cols = ", ".join(
                f"{quote_ident(p.column_name)} AS {quote_ident(p.name)}"
                for p in sorted(ds_props, key=lambda x: x.sort_order)
            )
            dataset = await db.get(Dataset, ds_id)
            if dataset is None or dataset.deleted_at is not None:
                raise OntologyValidationError(f"Dataset not found: {ds_id}")
            sql = f"SELECT {select_cols} FROM iceberg_scan(?, allow_moved_paths=true)"
            params.append(dataset.iceberg_location)
            if search and pk_prop.column_name:
                sql += f" WHERE CAST({quote_ident(pk_prop.column_name)} AS VARCHAR) ILIKE ?"
                params.append(f"%{search}%")
            return sql, params

        raise OntologyValidationError("Multi-dataset object types require full PK mapping")

    async def _get_active_type(self, db: AsyncSession, type_id: uuid.UUID) -> ObjectType:
        obj_type = await db.get(ObjectType, type_id)
        if obj_type is None or obj_type.deleted_at is not None:
            raise OntologyNotFoundError("Object type not found")
        return obj_type

    async def _get_active_property(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
    ) -> ObjectProperty:
        prop = await db.get(ObjectProperty, property_id)
        if prop is None or prop.deleted_at is not None:
            raise OntologyNotFoundError("Object property not found")
        return prop

    async def _get_active_link(self, db: AsyncSession, link_id: uuid.UUID) -> LinkType:
        link = await db.get(LinkType, link_id)
        if link is None or link.deleted_at is not None:
            raise OntologyNotFoundError("Link type not found")
        return link
