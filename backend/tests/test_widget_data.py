from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.analytics import Widget
from app.schemas.analytics import (
    BarChartWidgetConfig,
    FilterWidgetConfig,
    MetricAggregation,
    MetricWidgetConfig,
    WidgetDataRequest,
    WidgetDataResponse,
    WidgetType,
)
from app.services.analytics_service import AnalyticsService, AnalyticsValidationError


def test_parse_dataset_binding_requires_dataset() -> None:
    service = AnalyticsService()
    widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.TABLE.value,
        title="Test",
        config_json={},
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(AnalyticsValidationError, match="dataset binding"):
        service._parse_dataset_binding(widget)


def test_parse_dataset_binding_rejects_ontology_query() -> None:
    service = AnalyticsService()
    widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.METRIC_CARD.value,
        title="Test",
        config_json={},
        data_binding_json={"source_type": "ontology_query", "object_type_id": str(uuid.uuid4())},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(AnalyticsValidationError, match="ontology_query"):
        service._parse_dataset_binding(widget)


def test_query_metric_sum_requires_value_column() -> None:
    service = AnalyticsService()
    config = MetricWidgetConfig(aggregation=MetricAggregation.SUM)
    with pytest.raises(AnalyticsValidationError, match="value_column"):
        service._query_metric("s3://atlas-data/test", config)


def test_parse_bar_chart_requires_x_axis() -> None:
    service = AnalyticsService()
    widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.BAR_CHART.value,
        title="Chart",
        config_json={"aggregation": "sum", "y_axis": "qty"},
        data_binding_json={"source_type": "dataset", "dataset_id": str(uuid.uuid4())},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(AnalyticsValidationError, match="x_axis"):
        service._parse_bar_chart_config(widget)


def test_parse_bar_chart_sum_requires_y_axis() -> None:
    service = AnalyticsService()
    widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.BAR_CHART.value,
        title="Chart",
        config_json={"aggregation": "sum", "x_axis": "category"},
        data_binding_json={"source_type": "dataset", "dataset_id": str(uuid.uuid4())},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(AnalyticsValidationError, match="y_axis"):
        service._parse_bar_chart_config(widget)


@pytest.mark.asyncio
async def test_query_widget_data_bar_chart_returns_rows() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.BAR_CHART.value,
        title="Chart",
        config_json={
            "x_axis": "warehouse_id",
            "y_axis": "quantity_on_hand",
            "aggregation": "sum",
        },
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dataset = MagicMock()
    dataset.iceberg_location = "s3://atlas-data/test"

    mock_db = AsyncMock()

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_resolve_applicable_filters", AsyncMock(return_value=[])),
        patch.object(service, "_load_dataset_for_widget", AsyncMock(return_value=dataset)),
        patch.object(
            service,
            "_query_bar_chart",
            return_value=WidgetDataResponse(
                columns=["category", "value"],
                rows=[{"category": "A", "value": 10}],
                total=1,
            ),
        ),
    ):
        result = await service.query_widget_data(mock_db, widget_id, WidgetDataRequest())

    assert result.columns == ["category", "value"]
    assert result.rows == [{"category": "A", "value": 10}]


@pytest.mark.asyncio
async def test_query_widget_data_table_returns_shape() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.TABLE.value,
        title="Test",
        config_json={"page_size": 10},
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dataset = MagicMock()
    dataset.deleted_at = None
    dataset.iceberg_location = "s3://atlas-data/test"

    mock_db = AsyncMock()

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_resolve_applicable_filters", AsyncMock(return_value=[])),
        patch.object(service, "_load_dataset_for_widget", AsyncMock(return_value=dataset)),
        patch.object(
            service,
            "_query_iceberg_table",
            return_value=WidgetDataResponse(columns=["id"], rows=[{"id": 1}], total=1),
        ),
    ):
        result = await service.query_widget_data(mock_db, widget_id, WidgetDataRequest())

    assert result.columns == ["id"]
    assert result.rows == [{"id": 1}]
    assert result.total == 1


@pytest.mark.asyncio
async def test_query_widget_data_metric_returns_value() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.METRIC_CARD.value,
        title="Metric",
        config_json={"aggregation": "count"},
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dataset = MagicMock()
    dataset.iceberg_location = "s3://atlas-data/test"

    mock_db = AsyncMock()

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_resolve_applicable_filters", AsyncMock(return_value=[])),
        patch.object(service, "_load_dataset_for_widget", AsyncMock(return_value=dataset)),
        patch.object(
            service,
            "_query_metric",
            return_value=WidgetDataResponse(columns=["value"], rows=[{"value": 42}], total=1),
        ),
    ):
        result = await service.query_widget_data(mock_db, widget_id, WidgetDataRequest())

    assert result.rows == [{"value": 42}]


@pytest.mark.asyncio
async def test_query_widget_data_soft_deleted_dataset() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.TABLE.value,
        title="Test",
        config_json={},
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_db = AsyncMock()

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_resolve_applicable_filters", AsyncMock(return_value=[])),
        patch.object(
            service,
            "_load_dataset_for_widget",
            AsyncMock(side_effect=AnalyticsValidationError("Dataset not found")),
        ),
        pytest.raises(AnalyticsValidationError, match="Dataset not found"),
    ):
        await service.query_widget_data(mock_db, widget_id, WidgetDataRequest())


def test_parse_filter_requires_source_column() -> None:
    service = AnalyticsService()
    widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={"filter_type": "dropdown"},
        data_binding_json={"source_type": "dataset", "dataset_id": str(uuid.uuid4())},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(AnalyticsValidationError, match="source_column"):
        service._parse_filter_config(widget)


def test_build_merged_where_single_filter() -> None:
    service = AnalyticsService()
    from app.schemas.analytics import DataBinding

    filter_widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={
            "filter_type": "dropdown",
            "source_column": "warehouse_id",
            "applies_to": [],
        },
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    config = FilterWidgetConfig(source_column="warehouse_id")
    where_sql, where_params = service._build_merged_where(
        DataBinding(source_type="dataset"),
        [(filter_widget, config, "WH-EAST")],
    )
    assert where_sql == '"warehouse_id" = ?'
    assert where_params == ["WH-EAST"]


def test_build_merged_where_multi_select_uses_in() -> None:
    service = AnalyticsService()
    from app.schemas.analytics import DataBinding

    filter_widget = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={},
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    config = FilterWidgetConfig(source_column="region", multi_select=True)
    where_sql, where_params = service._build_merged_where(
        DataBinding(source_type="dataset"),
        [(filter_widget, config, ["A", "B"])],
    )
    assert where_sql == '"region" IN (?, ?)'
    assert where_params == ["A", "B"]


def test_build_merged_where_and_across_filters() -> None:
    service = AnalyticsService()
    from app.schemas.analytics import DataBinding

    fw1 = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="F1",
        config_json={},
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    fw2 = Widget(
        id=uuid.uuid4(),
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="F2",
        config_json={},
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    where_sql, where_params = service._build_merged_where(
        DataBinding(source_type="dataset"),
        [
            (fw1, FilterWidgetConfig(source_column="a"), "1"),
            (fw2, FilterWidgetConfig(source_column="b"), "2"),
        ],
    )
    assert where_sql == '"a" = ? AND "b" = ?'
    assert where_params == ["1", "2"]


@pytest.mark.asyncio
async def test_resolve_applicable_filters_ignores_not_in_applies_to() -> None:
    service = AnalyticsService()
    dashboard_id = uuid.uuid4()
    target_id = uuid.uuid4()
    filter_id = uuid.uuid4()

    filter_widget = Widget(
        id=filter_id,
        dashboard_id=dashboard_id,
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={
            "filter_type": "dropdown",
            "source_column": "warehouse_id",
            "applies_to": [str(uuid.uuid4())],
        },
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [filter_widget]
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    body = WidgetDataRequest(filters={str(filter_id): "WH-EAST"})
    applicable = await service._resolve_applicable_filters(
        mock_db, dashboard_id, target_id, body
    )
    assert applicable == []


@pytest.mark.asyncio
async def test_query_widget_data_filter_dropdown_returns_values() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={"filter_type": "dropdown", "source_column": "warehouse_id"},
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dataset = MagicMock()
    dataset.iceberg_location = "s3://atlas-data/test"
    mock_db = AsyncMock()

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_load_dataset_for_widget", AsyncMock(return_value=dataset)),
        patch.object(
            service,
            "_query_filter_dropdown",
            return_value=WidgetDataResponse(
                columns=["value"],
                rows=[{"value": "WH-EAST"}, {"value": "WH-WEST"}],
                total=2,
            ),
        ),
    ):
        result = await service.query_widget_data(mock_db, widget_id, WidgetDataRequest())

    assert result.rows == [{"value": "WH-EAST"}, {"value": "WH-WEST"}]


@pytest.mark.asyncio
async def test_query_widget_data_table_passes_merged_where() -> None:
    service = AnalyticsService()
    widget_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    filter_id = uuid.uuid4()
    widget = Widget(
        id=widget_id,
        dashboard_id=uuid.uuid4(),
        widget_type=WidgetType.TABLE.value,
        title="Table",
        config_json={"page_size": 10},
        data_binding_json={"source_type": "dataset", "dataset_id": str(dataset_id)},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    filter_widget = Widget(
        id=filter_id,
        dashboard_id=widget.dashboard_id,
        widget_type=WidgetType.FILTER.value,
        title="Filter",
        config_json={
            "filter_type": "dropdown",
            "source_column": "warehouse_id",
            "applies_to": [str(widget_id)],
        },
        data_binding_json=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dataset = MagicMock()
    dataset.iceberg_location = "s3://atlas-data/test"
    mock_db = AsyncMock()
    filter_config = FilterWidgetConfig(source_column="warehouse_id", applies_to=[widget_id])
    applicable = [(filter_widget, filter_config, "WH-EAST")]

    query_mock = MagicMock(
        return_value=WidgetDataResponse(columns=["id"], rows=[{"id": 1}], total=1)
    )

    with (
        patch.object(service, "_get_active_widget", AsyncMock(return_value=widget)),
        patch.object(service, "_get_active_dashboard", AsyncMock(return_value=MagicMock())),
        patch.object(service, "_resolve_applicable_filters", AsyncMock(return_value=applicable)),
        patch.object(service, "_load_dataset_for_widget", AsyncMock(return_value=dataset)),
        patch.object(service, "_query_iceberg_table", query_mock),
    ):
        await service.query_widget_data(
            mock_db,
            widget_id,
            WidgetDataRequest(filters={str(filter_id): "WH-EAST"}),
        )

    query_mock.assert_called_once()
    call_kwargs = query_mock.call_args.kwargs
    assert call_kwargs["where_sql"] == '"warehouse_id" = ?'
    assert call_kwargs["where_params"] == ["WH-EAST"]
