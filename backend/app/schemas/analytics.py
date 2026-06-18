from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WidgetType(str, Enum):
    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    METRIC_CARD = "metric_card"
    TEXT = "text"
    FILTER = "filter"


class LayoutItem(BaseModel):
    widget_id: UUID
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1, le=12)
    h: int = Field(ge=1)


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class DashboardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    layout_json: list[LayoutItem] | None = None


class DashboardResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    layout_json: list[LayoutItem]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WidgetCreate(BaseModel):
    widget_type: WidgetType
    title: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    data_binding_json: dict[str, Any] | None = None


class WidgetUpdate(BaseModel):
    title: str | None = None
    config_json: dict[str, Any] | None = None
    data_binding_json: dict[str, Any] | None = None


class WidgetResponse(BaseModel):
    id: UUID
    dashboard_id: UUID
    widget_type: WidgetType
    title: str | None = None
    config_json: dict[str, Any]
    data_binding_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardDetailResponse(BaseModel):
    dashboard: DashboardResponse
    widgets: list[WidgetResponse]


class DataBinding(BaseModel):
    source_type: Literal["dataset"] = "dataset"
    dataset_id: UUID | None = None
    filters: list[dict[str, Any]] | None = None
    limit: int | None = None


class TableWidgetConfig(BaseModel):
    columns: list[str] | None = None
    page_size: int = Field(default=50, ge=1, le=1000)
    sortable: bool = False
    filterable: bool = False


class MetricAggregation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class MetricFormat(str, Enum):
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"


class MetricWidgetConfig(BaseModel):
    value_column: str | None = None
    aggregation: MetricAggregation = MetricAggregation.COUNT
    label: str | None = None
    format: MetricFormat = MetricFormat.NUMBER
    prefix: str = ""
    suffix: str = ""


class BarChartWidgetConfig(BaseModel):
    x_axis: str | None = None
    y_axis: str | None = None
    color_by: str | None = None
    aggregation: MetricAggregation = MetricAggregation.SUM


class FilterWidgetConfig(BaseModel):
    filter_type: Literal["dropdown"] = "dropdown"
    source_column: str | None = None
    label: str | None = None
    applies_to: list[UUID] = Field(default_factory=list)
    multi_select: bool = False


class WidgetDataRequest(BaseModel):
    filters: dict[str, Any] = Field(default_factory=dict)


class WidgetDataResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int
