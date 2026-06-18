from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Dashboard, Widget
from app.models.dataset import Dataset
from app.schemas.analytics import (
    BarChartWidgetConfig,
    DashboardCreate,
    DashboardDetailResponse,
    DashboardResponse,
    DashboardUpdate,
    DataBinding,
    FilterWidgetConfig,
    LayoutItem,
    MetricAggregation,
    MetricWidgetConfig,
    TableWidgetConfig,
    WidgetCreate,
    WidgetDataRequest,
    WidgetDataResponse,
    WidgetResponse,
    WidgetType,
    WidgetUpdate,
)
from app.services.audit_service import AuditService
from app.services.dataset_service import DatasetNotFoundError, _serialize_value, quote_ident
from app.compute.duckdb_engine import DuckDBEngine


class AnalyticsNotFoundError(Exception):
    pass


class AnalyticsValidationError(Exception):
    pass


class AnalyticsService:
    def __init__(self) -> None:
        self._audit = AuditService()

    def _dashboard_to_response(self, dashboard: Dashboard) -> DashboardResponse:
        layout = [LayoutItem.model_validate(item) for item in (dashboard.layout_json or [])]
        return DashboardResponse(
            id=dashboard.id,
            name=dashboard.name,
            description=dashboard.description,
            layout_json=layout,
            is_public=dashboard.is_public,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )

    def _widget_to_response(self, widget: Widget) -> WidgetResponse:
        return WidgetResponse(
            id=widget.id,
            dashboard_id=widget.dashboard_id,
            widget_type=WidgetType(widget.widget_type),
            title=widget.title,
            config_json=widget.config_json or {},
            data_binding_json=widget.data_binding_json,
            created_at=widget.created_at,
            updated_at=widget.updated_at,
        )

    async def _get_active_dashboard(self, db: AsyncSession, dashboard_id: uuid.UUID) -> Dashboard:
        result = await db.execute(
            select(Dashboard).where(
                Dashboard.id == dashboard_id,
                Dashboard.deleted_at.is_(None),
            )
        )
        dashboard = result.scalar_one_or_none()
        if dashboard is None:
            raise AnalyticsNotFoundError("Dashboard not found")
        return dashboard

    async def _get_active_widget(self, db: AsyncSession, widget_id: uuid.UUID) -> Widget:
        result = await db.execute(
            select(Widget).where(
                Widget.id == widget_id,
                Widget.deleted_at.is_(None),
            )
        )
        widget = result.scalar_one_or_none()
        if widget is None:
            raise AnalyticsNotFoundError("Widget not found")
        return widget

    async def _validate_layout_widget_ids(
        self,
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        layout: list[LayoutItem],
    ) -> None:
        if not layout:
            return
        widget_ids = {item.widget_id for item in layout}
        result = await db.execute(
            select(Widget.id).where(
                Widget.dashboard_id == dashboard_id,
                Widget.deleted_at.is_(None),
                Widget.id.in_(widget_ids),
            )
        )
        found = set(result.scalars().all())
        if found != widget_ids:
            raise AnalyticsValidationError("layout_json references unknown or deleted widgets")

    async def list_dashboards(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DashboardResponse], dict[str, Any]]:
        query = select(Dashboard).where(Dashboard.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Dashboard).where(
            Dashboard.deleted_at.is_(None)
        )

        total = (await db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await db.execute(
            query.order_by(Dashboard.created_at.desc()).offset(offset).limit(page_size)
        )
        dashboards = result.scalars().all()
        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / page_size)) if total else 0,
        }
        return [self._dashboard_to_response(d) for d in dashboards], meta

    async def create_dashboard(
        self,
        db: AsyncSession,
        body: DashboardCreate,
    ) -> DashboardResponse:
        async with db.begin():
            dashboard = Dashboard(
                name=body.name,
                description=body.description,
                layout_json=[],
            )
            db.add(dashboard)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="dashboard",
                entity_id=dashboard.id,
                payload={"name": dashboard.name},
            )
        return await self.get_dashboard(db, dashboard.id)

    async def get_dashboard(self, db: AsyncSession, dashboard_id: uuid.UUID) -> DashboardResponse:
        dashboard = await self._get_active_dashboard(db, dashboard_id)
        return self._dashboard_to_response(dashboard)

    async def get_dashboard_detail(
        self,
        db: AsyncSession,
        dashboard_id: uuid.UUID,
    ) -> DashboardDetailResponse:
        dashboard = await self._get_active_dashboard(db, dashboard_id)
        result = await db.execute(
            select(Widget)
            .where(
                Widget.dashboard_id == dashboard_id,
                Widget.deleted_at.is_(None),
            )
            .order_by(Widget.created_at.asc())
        )
        widgets = result.scalars().all()
        return DashboardDetailResponse(
            dashboard=self._dashboard_to_response(dashboard),
            widgets=[self._widget_to_response(w) for w in widgets],
        )

    async def update_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        body: DashboardUpdate,
    ) -> DashboardResponse:
        async with db.begin():
            dashboard = await self._get_active_dashboard(db, dashboard_id)
            changes: dict[str, Any] = {}

            if body.name is not None:
                changes["name"] = body.name
                dashboard.name = body.name
            if body.description is not None:
                changes["description"] = body.description
                dashboard.description = body.description
            if body.layout_json is not None:
                await self._validate_layout_widget_ids(db, dashboard_id, body.layout_json)
                changes["layout_json"] = [item.model_dump(mode="json") for item in body.layout_json]
                dashboard.layout_json = changes["layout_json"]

            if not changes:
                return self._dashboard_to_response(dashboard)

            dashboard.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="dashboard",
                entity_id=dashboard.id,
                payload=changes,
            )
        return await self.get_dashboard(db, dashboard_id)

    async def delete_dashboard(self, db: AsyncSession, dashboard_id: uuid.UUID) -> None:
        async with db.begin():
            dashboard = await self._get_active_dashboard(db, dashboard_id)
            dashboard.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="dashboard",
                entity_id=dashboard.id,
            )

    async def create_widget(
        self,
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        body: WidgetCreate,
    ) -> WidgetResponse:
        async with db.begin():
            await self._get_active_dashboard(db, dashboard_id)
            widget = Widget(
                dashboard_id=dashboard_id,
                widget_type=body.widget_type.value,
                title=body.title,
                config_json=body.config_json,
                data_binding_json=body.data_binding_json,
            )
            db.add(widget)
            await db.flush()
            await self._audit.write(
                db,
                action="create",
                entity_type="widget",
                entity_id=widget.id,
                payload={"dashboard_id": str(dashboard_id), "widget_type": widget.widget_type},
            )
        return self._widget_to_response(widget)

    async def update_widget(
        self,
        db: AsyncSession,
        widget_id: uuid.UUID,
        body: WidgetUpdate,
    ) -> WidgetResponse:
        async with db.begin():
            widget = await self._get_active_widget(db, widget_id)
            await self._get_active_dashboard(db, widget.dashboard_id)
            changes: dict[str, Any] = {}

            if body.title is not None:
                changes["title"] = body.title
                widget.title = body.title
            if body.config_json is not None:
                changes["config_json"] = body.config_json
                widget.config_json = body.config_json
            if body.data_binding_json is not None:
                changes["data_binding_json"] = body.data_binding_json
                widget.data_binding_json = body.data_binding_json

            if not changes:
                return self._widget_to_response(widget)

            widget.updated_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="update",
                entity_type="widget",
                entity_id=widget.id,
                payload=changes,
            )
        widget = await self._get_active_widget(db, widget_id)
        return self._widget_to_response(widget)

    async def delete_widget(self, db: AsyncSession, widget_id: uuid.UUID) -> None:
        async with db.begin():
            widget = await self._get_active_widget(db, widget_id)
            await self._get_active_dashboard(db, widget.dashboard_id)
            widget.deleted_at = datetime.now(timezone.utc)
            await self._audit.write(
                db,
                action="soft_delete",
                entity_type="widget",
                entity_id=widget.id,
            )

    def _parse_dataset_binding(self, widget: Widget) -> DataBinding:
        binding_raw = widget.data_binding_json or {}
        if binding_raw.get("source_type") == "ontology_query":
            raise AnalyticsValidationError("ontology_query binding is not supported in Phase 1")

        try:
            binding = DataBinding.model_validate(binding_raw)
        except Exception as exc:
            raise AnalyticsValidationError("Invalid data binding configuration") from exc

        if binding.source_type != "dataset":
            raise AnalyticsValidationError("Only dataset bindings are supported in Phase 1")
        if binding.dataset_id is None:
            raise AnalyticsValidationError("Widget requires a dataset binding")
        return binding

    def _parse_table_config(self, widget: Widget) -> tuple[DataBinding, TableWidgetConfig]:
        if widget.widget_type != WidgetType.TABLE.value:
            raise AnalyticsValidationError("Invalid widget type for table query")
        binding = self._parse_dataset_binding(widget)
        config = TableWidgetConfig.model_validate(widget.config_json or {})
        return binding, config

    def _parse_metric_config(self, widget: Widget) -> tuple[DataBinding, MetricWidgetConfig]:
        if widget.widget_type != WidgetType.METRIC_CARD.value:
            raise AnalyticsValidationError("Invalid widget type for metric query")
        binding = self._parse_dataset_binding(widget)
        config = MetricWidgetConfig.model_validate(widget.config_json or {})
        return binding, config

    def _parse_bar_chart_config(self, widget: Widget) -> tuple[DataBinding, BarChartWidgetConfig]:
        if widget.widget_type != WidgetType.BAR_CHART.value:
            raise AnalyticsValidationError("Invalid widget type for bar chart query")
        binding = self._parse_dataset_binding(widget)
        config = BarChartWidgetConfig.model_validate(widget.config_json or {})
        if not config.x_axis:
            raise AnalyticsValidationError("Bar chart requires x_axis")
        if config.aggregation in {
            MetricAggregation.SUM,
            MetricAggregation.AVG,
            MetricAggregation.MIN,
            MetricAggregation.MAX,
        } and not config.y_axis:
            raise AnalyticsValidationError(
                f"{config.aggregation.value} aggregation requires y_axis"
            )
        return binding, config

    def _parse_filter_config(self, widget: Widget) -> tuple[DataBinding, FilterWidgetConfig]:
        if widget.widget_type != WidgetType.FILTER.value:
            raise AnalyticsValidationError("Invalid widget type for filter query")
        binding = self._parse_dataset_binding(widget)
        config = FilterWidgetConfig.model_validate(widget.config_json or {})
        if config.filter_type != "dropdown":
            raise AnalyticsValidationError("Only dropdown filters are supported in Phase 1")
        if not config.source_column:
            raise AnalyticsValidationError("Filter requires source_column")
        return binding, config

    async def _resolve_applicable_filters(
        self,
        db: AsyncSession,
        dashboard_id: uuid.UUID,
        target_widget_id: uuid.UUID,
        body: WidgetDataRequest,
    ) -> list[tuple[Widget, FilterWidgetConfig, Any]]:
        result = await db.execute(
            select(Widget).where(
                Widget.dashboard_id == dashboard_id,
                Widget.deleted_at.is_(None),
                Widget.widget_type == WidgetType.FILTER.value,
            )
        )
        applicable: list[tuple[Widget, FilterWidgetConfig, Any]] = []
        for filter_widget in result.scalars().all():
            config = FilterWidgetConfig.model_validate(filter_widget.config_json or {})
            if target_widget_id not in config.applies_to:
                continue
            filter_key = str(filter_widget.id)
            if filter_key not in body.filters:
                continue
            value = body.filters[filter_key]
            if value is None or value == "" or value == []:
                continue
            applicable.append((filter_widget, config, value))
        return applicable

    def _binding_filter_clauses(
        self,
        binding_filters: list[dict[str, Any]] | None,
    ) -> tuple[list[str], list[Any]]:
        if not binding_filters:
            return [], []

        clauses: list[str] = []
        params: list[Any] = []
        for cond in binding_filters:
            column = quote_ident(str(cond["column"]))
            operator = cond.get("operator", "eq")
            value = cond.get("value")

            if operator == "eq":
                clauses.append(f"{column} = ?")
                params.append(value)
            elif operator == "neq":
                clauses.append(f"{column} <> ?")
                params.append(value)
            elif operator == "gt":
                clauses.append(f"{column} > ?")
                params.append(value)
            elif operator == "gte":
                clauses.append(f"{column} >= ?")
                params.append(value)
            elif operator == "lt":
                clauses.append(f"{column} < ?")
                params.append(value)
            elif operator == "lte":
                clauses.append(f"{column} <= ?")
                params.append(value)
            elif operator == "in":
                values = value if isinstance(value, list) else [value]
                placeholders = ", ".join("?" for _ in values)
                clauses.append(f"{column} IN ({placeholders})")
                params.extend(values)
            elif operator == "not_in":
                values = value if isinstance(value, list) else [value]
                placeholders = ", ".join("?" for _ in values)
                clauses.append(f"{column} NOT IN ({placeholders})")
                params.extend(values)
            elif operator == "is_null":
                clauses.append(f"{column} IS NULL")
            elif operator == "is_not_null":
                clauses.append(f"{column} IS NOT NULL")
            else:
                raise AnalyticsValidationError(f"Unknown filter operator: {operator}")
        return clauses, params

    def _widget_filter_clauses(
        self,
        applicable_filters: list[tuple[Widget, FilterWidgetConfig, Any]],
    ) -> tuple[list[str], list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for _filter_widget, config, value in applicable_filters:
            column = quote_ident(config.source_column or "")
            if isinstance(value, list):
                if not value:
                    continue
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{column} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{column} = ?")
                params.append(value)
        return clauses, params

    def _build_merged_where(
        self,
        binding: DataBinding,
        applicable_filters: list[tuple[Widget, FilterWidgetConfig, Any]],
    ) -> tuple[str | None, list[Any]]:
        binding_clauses, binding_params = self._binding_filter_clauses(binding.filters)
        widget_clauses, widget_params = self._widget_filter_clauses(applicable_filters)
        all_clauses = binding_clauses + widget_clauses
        if not all_clauses:
            return None, []
        return " AND ".join(all_clauses), binding_params + widget_params

    async def _load_dataset_for_widget(self, db: AsyncSession, binding: DataBinding) -> Dataset:
        try:
            return await self._get_active_dataset(db, binding.dataset_id)
        except DatasetNotFoundError as exc:
            raise AnalyticsValidationError(str(exc)) from exc

    async def _get_active_dataset(self, db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None or dataset.deleted_at is not None:
            raise DatasetNotFoundError("Dataset not found")
        return dataset

    def _query_iceberg_table(
        self,
        iceberg_location: str,
        *,
        columns: list[str] | None,
        page_size: int,
        where_sql: str | None = None,
        where_params: list[Any] | None = None,
    ) -> WidgetDataResponse:
        engine = DuckDBEngine()
        where_params = where_params or []
        where_clause = f" WHERE {where_sql}" if where_sql else ""
        try:
            if columns:
                select_cols = ", ".join(quote_ident(col) for col in columns)
            else:
                select_cols = "*"

            result = engine._conn.execute(
                f"SELECT {select_cols} FROM iceberg_scan(?, allow_moved_paths=true)"
                f"{where_clause} LIMIT {int(page_size)}",
                [iceberg_location, *where_params],
            ).fetch_arrow_table()

            count_result = engine._conn.execute(
                f"SELECT COUNT(*) AS cnt FROM iceberg_scan(?, allow_moved_paths=true){where_clause}",
                [iceberg_location, *where_params],
            ).fetchone()
            total = int(count_result[0]) if count_result else 0
        finally:
            engine.close()

        col_names = [f.name for f in result.schema]
        rows = [
            {col: _serialize_value(result[col][i].as_py()) for col in col_names}
            for i in range(result.num_rows)
        ]
        return WidgetDataResponse(columns=col_names, rows=rows, total=total)

    def _query_metric(
        self,
        iceberg_location: str,
        config: MetricWidgetConfig,
        *,
        where_sql: str | None = None,
        where_params: list[Any] | None = None,
    ) -> WidgetDataResponse:
        where_params = where_params or []
        aggregation = config.aggregation
        value_column = config.value_column

        if aggregation in {
            MetricAggregation.SUM,
            MetricAggregation.AVG,
            MetricAggregation.MIN,
            MetricAggregation.MAX,
        } and not value_column:
            raise AnalyticsValidationError(
                f"{aggregation.value} aggregation requires value_column"
            )

        if aggregation == MetricAggregation.COUNT:
            if value_column:
                expr = f"COUNT({quote_ident(value_column)})"
            else:
                expr = "COUNT(*)"
        else:
            col = quote_ident(value_column or "")
            expr = f"{aggregation.value.upper()}({col})"

        where_clause = f" WHERE {where_sql}" if where_sql else ""
        sql = (
            f"SELECT {expr} AS value FROM iceberg_scan(?, allow_moved_paths=true){where_clause}"
        )

        engine = DuckDBEngine()
        try:
            result = engine._conn.execute(sql, [iceberg_location, *where_params]).fetchone()
        finally:
            engine.close()

        raw_value = result[0] if result else None
        value = _serialize_value(raw_value)
        if value is None:
            value = 0
        return WidgetDataResponse(columns=["value"], rows=[{"value": value}], total=1)

    def _query_bar_chart(
        self,
        iceberg_location: str,
        config: BarChartWidgetConfig,
        *,
        where_sql: str | None = None,
        where_params: list[Any] | None = None,
    ) -> WidgetDataResponse:
        where_params = where_params or []
        x_col = quote_ident(config.x_axis or "")
        aggregation = config.aggregation

        if aggregation == MetricAggregation.COUNT:
            if config.y_axis:
                agg_expr = f"COUNT({quote_ident(config.y_axis)})"
            else:
                agg_expr = "COUNT(*)"
        else:
            y_col = quote_ident(config.y_axis or "")
            agg_expr = f"{aggregation.value.upper()}({y_col})"

        base_where = f"{x_col} IS NOT NULL AND CAST({x_col} AS VARCHAR) != ''"
        if where_sql:
            full_where = f"{base_where} AND {where_sql}"
        else:
            full_where = base_where

        sql = f"""
            SELECT {x_col} AS category, {agg_expr} AS value
            FROM iceberg_scan(?, allow_moved_paths=true)
            WHERE {full_where}
            GROUP BY {x_col}
            ORDER BY category
            LIMIT 100
        """

        engine = DuckDBEngine()
        try:
            result = engine._conn.execute(sql, [iceberg_location, *where_params]).fetch_arrow_table()
        finally:
            engine.close()

        rows = [
            {
                "category": _serialize_value(result["category"][i].as_py()),
                "value": _serialize_value(result["value"][i].as_py()),
            }
            for i in range(result.num_rows)
        ]
        return WidgetDataResponse(columns=["category", "value"], rows=rows, total=len(rows))

    def _query_filter_dropdown(
        self,
        iceberg_location: str,
        source_column: str,
    ) -> WidgetDataResponse:
        col = quote_ident(source_column)
        sql = f"""
            SELECT DISTINCT {col} AS value
            FROM iceberg_scan(?, allow_moved_paths=true)
            WHERE {col} IS NOT NULL AND CAST({col} AS VARCHAR) != ''
            ORDER BY value
            LIMIT 500
        """
        engine = DuckDBEngine()
        try:
            result = engine._conn.execute(sql, [iceberg_location]).fetch_arrow_table()
        finally:
            engine.close()

        rows = [
            {"value": _serialize_value(result["value"][i].as_py())}
            for i in range(result.num_rows)
        ]
        return WidgetDataResponse(columns=["value"], rows=rows, total=len(rows))

    async def query_widget_data(
        self,
        db: AsyncSession,
        widget_id: uuid.UUID,
        body: WidgetDataRequest,
    ) -> WidgetDataResponse:
        widget = await self._get_active_widget(db, widget_id)
        await self._get_active_dashboard(db, widget.dashboard_id)

        if widget.widget_type == WidgetType.FILTER.value:
            binding, config = self._parse_filter_config(widget)
            dataset = await self._load_dataset_for_widget(db, binding)
            return self._query_filter_dropdown(dataset.iceberg_location, config.source_column or "")

        applicable_filters = await self._resolve_applicable_filters(
            db,
            widget.dashboard_id,
            widget.id,
            body,
        )

        if widget.widget_type == WidgetType.TABLE.value:
            binding, config = self._parse_table_config(widget)
            dataset = await self._load_dataset_for_widget(db, binding)
            where_sql, where_params = self._build_merged_where(binding, applicable_filters)
            return self._query_iceberg_table(
                dataset.iceberg_location,
                columns=config.columns,
                page_size=config.page_size,
                where_sql=where_sql,
                where_params=where_params,
            )

        if widget.widget_type == WidgetType.METRIC_CARD.value:
            binding, config = self._parse_metric_config(widget)
            dataset = await self._load_dataset_for_widget(db, binding)
            where_sql, where_params = self._build_merged_where(binding, applicable_filters)
            return self._query_metric(
                dataset.iceberg_location,
                config,
                where_sql=where_sql,
                where_params=where_params,
            )

        if widget.widget_type == WidgetType.BAR_CHART.value:
            binding, config = self._parse_bar_chart_config(widget)
            dataset = await self._load_dataset_for_widget(db, binding)
            where_sql, where_params = self._build_merged_where(binding, applicable_filters)
            return self._query_bar_chart(
                dataset.iceberg_location,
                config,
                where_sql=where_sql,
                where_params=where_params,
            )

        raise AnalyticsValidationError(
            f"Widget data queries are not supported for widget type {widget.widget_type}"
        )
