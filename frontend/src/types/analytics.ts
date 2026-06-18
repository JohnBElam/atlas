export type WidgetType =
  | "table"
  | "bar_chart"
  | "line_chart"
  | "pie_chart"
  | "metric_card"
  | "text"
  | "filter";

export interface LayoutItem {
  widget_id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  layout_json: LayoutItem[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface Widget {
  id: string;
  dashboard_id: string;
  widget_type: WidgetType;
  title: string | null;
  config_json: Record<string, unknown>;
  data_binding_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardDetail {
  dashboard: Dashboard;
  widgets: Widget[];
}

export interface DataBinding {
  source_type: "dataset";
  dataset_id?: string;
  filters?: Record<string, unknown>[];
  limit?: number;
}

export interface TableWidgetConfig {
  columns: string[] | null;
  page_size: number;
  sortable: boolean;
  filterable: boolean;
}

export const DEFAULT_TABLE_CONFIG: TableWidgetConfig = {
  columns: null,
  page_size: 50,
  sortable: false,
  filterable: false,
};

export interface WidgetData {
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
}

export type WidgetFilterState = Record<string, unknown>;

export function parseTableConfig(config: Record<string, unknown>): TableWidgetConfig {
  return {
    columns: Array.isArray(config.columns)
      ? config.columns.filter((c): c is string => typeof c === "string")
      : null,
    page_size: typeof config.page_size === "number" ? config.page_size : DEFAULT_TABLE_CONFIG.page_size,
    sortable: config.sortable === true,
    filterable: config.filterable === true,
  };
}

export function parseDataBinding(binding: Record<string, unknown> | null): DataBinding | null {
  if (!binding || binding.source_type !== "dataset") {
    return null;
  }
  return {
    source_type: "dataset",
    dataset_id: typeof binding.dataset_id === "string" ? binding.dataset_id : undefined,
    filters: Array.isArray(binding.filters) ? binding.filters : undefined,
    limit: typeof binding.limit === "number" ? binding.limit : undefined,
  };
}

export type MetricAggregation = "count" | "sum" | "avg" | "min" | "max";
export type MetricFormat = "number" | "currency" | "percentage";

export interface MetricWidgetConfig {
  value_column: string | null;
  aggregation: MetricAggregation;
  label: string | null;
  format: MetricFormat;
  prefix: string;
  suffix: string;
}

export const DEFAULT_METRIC_CONFIG: MetricWidgetConfig = {
  value_column: null,
  aggregation: "count",
  label: null,
  format: "number",
  prefix: "",
  suffix: "",
};

const METRIC_AGGREGATIONS: MetricAggregation[] = ["count", "sum", "avg", "min", "max"];
const METRIC_FORMATS: MetricFormat[] = ["number", "currency", "percentage"];

export function parseMetricConfig(config: Record<string, unknown>): MetricWidgetConfig {
  const aggregation = METRIC_AGGREGATIONS.includes(config.aggregation as MetricAggregation)
    ? (config.aggregation as MetricAggregation)
    : DEFAULT_METRIC_CONFIG.aggregation;
  const format = METRIC_FORMATS.includes(config.format as MetricFormat)
    ? (config.format as MetricFormat)
    : DEFAULT_METRIC_CONFIG.format;
  return {
    value_column: typeof config.value_column === "string" ? config.value_column : null,
    aggregation,
    label: typeof config.label === "string" ? config.label : null,
    format,
    prefix: typeof config.prefix === "string" ? config.prefix : "",
    suffix: typeof config.suffix === "string" ? config.suffix : "",
  };
}

export function formatMetricValue(
  value: unknown,
  config: Pick<MetricWidgetConfig, "format" | "prefix" | "suffix">,
): string {
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) {
    return "—";
  }

  let formatted: string;
  if (config.format === "percentage") {
    formatted = `${(num * 100).toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
  } else if (config.format === "currency") {
    const prefix = config.prefix || "$";
    formatted = `${prefix}${num.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    if (config.suffix) formatted += config.suffix;
    return formatted;
  } else {
    formatted = num.toLocaleString();
  }

  return `${config.prefix}${formatted}${config.suffix}`;
}

export interface BarChartWidgetConfig {
  x_axis: string | null;
  y_axis: string | null;
  color_by: string | null;
  aggregation: MetricAggregation;
}

export const DEFAULT_BAR_CHART_CONFIG: BarChartWidgetConfig = {
  x_axis: null,
  y_axis: null,
  color_by: null,
  aggregation: "sum",
};

export function parseBarChartConfig(config: Record<string, unknown>): BarChartWidgetConfig {
  const aggregation = METRIC_AGGREGATIONS.includes(config.aggregation as MetricAggregation)
    ? (config.aggregation as MetricAggregation)
    : DEFAULT_BAR_CHART_CONFIG.aggregation;
  return {
    x_axis: typeof config.x_axis === "string" ? config.x_axis : null,
    y_axis: typeof config.y_axis === "string" ? config.y_axis : null,
    color_by: typeof config.color_by === "string" ? config.color_by : null,
    aggregation,
  };
}

export interface FilterWidgetConfig {
  filter_type: "dropdown";
  source_column: string | null;
  label: string | null;
  applies_to: string[];
  multi_select: boolean;
}

export const DEFAULT_FILTER_CONFIG: FilterWidgetConfig = {
  filter_type: "dropdown",
  source_column: null,
  label: null,
  applies_to: [],
  multi_select: false,
};

export function parseFilterConfig(config: Record<string, unknown>): FilterWidgetConfig {
  const appliesTo = Array.isArray(config.applies_to)
    ? config.applies_to.filter((id): id is string => typeof id === "string")
    : [];
  return {
    filter_type: "dropdown",
    source_column: typeof config.source_column === "string" ? config.source_column : null,
    label: typeof config.label === "string" ? config.label : null,
    applies_to: appliesTo,
    multi_select: config.multi_select === true,
  };
}

export function buildApplicableFilters(
  targetWidgetId: string,
  widgets: Widget[],
  filterState: Record<string, string | string[]>,
): WidgetFilterState {
  const applicable: WidgetFilterState = {};
  for (const widget of widgets) {
    if (widget.widget_type !== "filter") continue;
    const config = parseFilterConfig(widget.config_json);
    if (!config.applies_to.includes(targetWidgetId)) continue;
    const value = filterState[widget.id];
    if (value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) {
      continue;
    }
    applicable[widget.id] = value;
  }
  return applicable;
}

export interface TextWidgetConfig {
  content: string;
}

export const DEFAULT_TEXT_CONFIG: TextWidgetConfig = { content: "" };

export function parseTextConfig(config: Record<string, unknown>): TextWidgetConfig {
  return { content: typeof config.content === "string" ? config.content : "" };
}
