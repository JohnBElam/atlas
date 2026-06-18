import { useEffect, useState } from "react";
import { useDatasets, useDataset } from "@/api/datasets";
import { useUpdateWidget } from "@/api/analytics";
import { Input } from "@/components/ui/Input";
import { getErrorMessage } from "@/lib/errors";
import {
  DEFAULT_BAR_CHART_CONFIG,
  DEFAULT_FILTER_CONFIG,
  DEFAULT_METRIC_CONFIG,
  DEFAULT_TABLE_CONFIG,
  DEFAULT_TEXT_CONFIG,
  parseBarChartConfig,
  parseDataBinding,
  parseFilterConfig,
  parseMetricConfig,
  parseTableConfig,
  parseTextConfig,
  type BarChartWidgetConfig,
  type DataBinding,
  type FilterWidgetConfig,
  type MetricAggregation,
  type MetricFormat,
  type MetricWidgetConfig,
  type TableWidgetConfig,
  type TextWidgetConfig,
  type Widget,
} from "@/types/analytics";

type ConfigTab = "general" | "binding" | "display";

const AGGREGATIONS: MetricAggregation[] = ["count", "sum", "avg", "min", "max"];
const FORMATS: MetricFormat[] = ["number", "currency", "percentage"];

export function WidgetConfigPanel({
  dashboardId,
  widget,
  widgets,
}: {
  dashboardId: string;
  widget: Widget | null;
  widgets: Widget[];
}) {
  const [tab, setTab] = useState<ConfigTab>("general");
  const [title, setTitle] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [tableConfig, setTableConfig] = useState<TableWidgetConfig>(DEFAULT_TABLE_CONFIG);
  const [metricConfig, setMetricConfig] = useState<MetricWidgetConfig>(DEFAULT_METRIC_CONFIG);
  const [barChartConfig, setBarChartConfig] =
    useState<BarChartWidgetConfig>(DEFAULT_BAR_CHART_CONFIG);
  const [filterConfig, setFilterConfig] = useState<FilterWidgetConfig>(DEFAULT_FILTER_CONFIG);
  const [textConfig, setTextConfig] = useState<TextWidgetConfig>(DEFAULT_TEXT_CONFIG);
  const [saveError, setSaveError] = useState<string | null>(null);

  const { data: datasets } = useDatasets();
  const { data: dataset } = useDataset(datasetId);
  const updateWidget = useUpdateWidget(dashboardId);

  useEffect(() => {
    if (!widget) return;
    setTitle(widget.title ?? "");
    const binding = parseDataBinding(widget.data_binding_json);
    setDatasetId(binding?.dataset_id ?? "");
    if (widget.widget_type === "table") {
      setTableConfig(parseTableConfig(widget.config_json));
    }
    if (widget.widget_type === "metric_card") {
      setMetricConfig(parseMetricConfig(widget.config_json));
    }
    if (widget.widget_type === "bar_chart") {
      setBarChartConfig(parseBarChartConfig(widget.config_json));
    }
    if (widget.widget_type === "filter") {
      setFilterConfig(parseFilterConfig(widget.config_json));
    }
    if (widget.widget_type === "text") {
      setTextConfig(parseTextConfig(widget.config_json));
    }
    setSaveError(null);
  }, [widget]);

  if (!widget) {
    return (
      <aside className="border border-zinc-700 bg-zinc-900 p-4">
        <p className="text-sm text-zinc-500">Select a widget to configure.</p>
      </aside>
    );
  }

  if (
    widget.widget_type !== "table" &&
    widget.widget_type !== "metric_card" &&
    widget.widget_type !== "bar_chart" &&
    widget.widget_type !== "filter" &&
    widget.widget_type !== "text"
  ) {
    return (
      <aside className="border border-zinc-700 bg-zinc-900 p-4">
        <p className="text-sm text-zinc-500">This widget type is not configurable yet.</p>
      </aside>
    );
  }

  const schemaColumns =
    dataset?.schema_json?.fields?.map((field) => field.name).filter(Boolean) ?? [];

  const persist = (patch: {
    title?: string;
    data_binding_json?: DataBinding | null;
    config_json?: TableWidgetConfig | MetricWidgetConfig | BarChartWidgetConfig | FilterWidgetConfig | TextWidgetConfig;
  }) => {
    setSaveError(null);
    updateWidget.mutate(
      {
        widgetId: widget.id,
        body: {
          ...(patch.title !== undefined ? { title: patch.title } : {}),
          ...(patch.data_binding_json !== undefined
            ? {
                data_binding_json: patch.data_binding_json as unknown as Record<
                  string,
                  unknown
                > | null,
              }
            : {}),
          ...(patch.config_json !== undefined
            ? { config_json: patch.config_json as unknown as Record<string, unknown> }
            : {}),
        },
      },
      { onError: (err) => setSaveError(getErrorMessage(err)) },
    );
  };

  const tabs: { id: ConfigTab; label: string }[] =
    widget.widget_type === "text"
      ? [
          { id: "general", label: "General" },
          { id: "display", label: "Display" },
        ]
      : [
          { id: "general", label: "General" },
          { id: "binding", label: "Data Binding" },
          { id: "display", label: "Display" },
        ];

  const columnRequired =
    (widget.widget_type === "metric_card" && metricConfig.aggregation !== "count") ||
    (widget.widget_type === "bar_chart" && barChartConfig.aggregation !== "count");

  const targetWidgets = widgets.filter(
    (w) => w.id !== widget.id && w.widget_type !== "filter",
  );

  return (
    <aside className="flex flex-col border border-zinc-700 bg-zinc-900">
      <div className="flex border-b border-zinc-700">
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            className={`flex-1 px-2 py-2 text-xs ${
              tab === id
                ? "border-b-2 border-indigo-500 text-indigo-300"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="space-y-4 p-4">
        {tab === "general" && (
          <label className="block space-y-1">
            <span className="text-xs text-zinc-500">Title</span>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => {
                if (title !== (widget.title ?? "")) {
                  persist({ title });
                }
              }}
            />
          </label>
        )}

        {tab === "binding" && widget.widget_type !== "text" && (
          <label className="block space-y-1">
            <span className="text-xs text-zinc-500">Dataset</span>
            <select
              className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
              value={datasetId}
              onChange={(e) => {
                const nextId = e.target.value;
                setDatasetId(nextId);
                const binding: DataBinding | null = nextId
                  ? { source_type: "dataset", dataset_id: nextId }
                  : null;
                persist({ data_binding_json: binding });
              }}
            >
              <option value="">Select dataset…</option>
              {datasets?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.display_name}
                </option>
              ))}
            </select>
          </label>
        )}

        {tab === "display" && widget.widget_type === "table" && (
          <>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Page size</span>
              <Input
                type="number"
                min={1}
                max={1000}
                value={tableConfig.page_size}
                onChange={(e) => {
                  const pageSize = Number(e.target.value) || DEFAULT_TABLE_CONFIG.page_size;
                  setTableConfig({ ...tableConfig, page_size: pageSize });
                }}
                onBlur={(e) => {
                  const pageSize = Number(e.target.value) || DEFAULT_TABLE_CONFIG.page_size;
                  const next = { ...tableConfig, page_size: pageSize };
                  setTableConfig(next);
                  persist({ config_json: next });
                }}
              />
            </label>
            {schemaColumns.length > 0 && (
              <fieldset className="space-y-2">
                <legend className="text-xs text-zinc-500">Columns (empty = all)</legend>
                <div className="max-h-40 space-y-1 overflow-auto">
                  {schemaColumns.map((col) => {
                    const selected =
                      tableConfig.columns === null || tableConfig.columns.includes(col);
                    return (
                      <label key={col} className="flex items-center gap-2 text-xs text-zinc-300">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={(e) => {
                            const allCols = schemaColumns;
                            let nextColumns: string[] | null;
                            if (e.target.checked) {
                              const current =
                                tableConfig.columns === null
                                  ? [...allCols]
                                  : [...tableConfig.columns];
                              if (!current.includes(col)) current.push(col);
                              nextColumns = current.length === allCols.length ? null : current;
                            } else {
                              const current =
                                tableConfig.columns === null
                                  ? allCols.filter((c) => c !== col)
                                  : tableConfig.columns.filter((c) => c !== col);
                              nextColumns = current.length === 0 ? null : current;
                            }
                            const next = { ...tableConfig, columns: nextColumns };
                            setTableConfig(next);
                            persist({ config_json: next });
                          }}
                        />
                        <span className="font-data">{col}</span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            )}
          </>
        )}

        {tab === "display" && widget.widget_type === "metric_card" && (
          <>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Label</span>
              <Input
                value={metricConfig.label ?? ""}
                onChange={(e) =>
                  setMetricConfig({ ...metricConfig, label: e.target.value || null })
                }
                onBlur={() => persist({ config_json: metricConfig })}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Aggregation</span>
              <select
                className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                value={metricConfig.aggregation}
                onChange={(e) => {
                  const next = {
                    ...metricConfig,
                    aggregation: e.target.value as MetricAggregation,
                  };
                  setMetricConfig(next);
                  persist({ config_json: next });
                }}
              >
                {AGGREGATIONS.map((agg) => (
                  <option key={agg} value={agg}>
                    {agg}
                  </option>
                ))}
              </select>
            </label>
            {schemaColumns.length > 0 && (
              <label className="block space-y-1">
                <span className="text-xs text-zinc-500">
                  Value column{columnRequired ? "" : " (optional for count)"}
                </span>
                <select
                  className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                  value={metricConfig.value_column ?? ""}
                  onChange={(e) => {
                    const next = {
                      ...metricConfig,
                      value_column: e.target.value || null,
                    };
                    setMetricConfig(next);
                    persist({ config_json: next });
                  }}
                >
                  <option value="">—</option>
                  {schemaColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Format</span>
              <select
                className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                value={metricConfig.format}
                onChange={(e) => {
                  const next = {
                    ...metricConfig,
                    format: e.target.value as MetricFormat,
                  };
                  setMetricConfig(next);
                  persist({ config_json: next });
                }}
              >
                {FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Prefix</span>
              <Input
                value={metricConfig.prefix}
                onChange={(e) =>
                  setMetricConfig({ ...metricConfig, prefix: e.target.value })
                }
                onBlur={() => persist({ config_json: metricConfig })}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Suffix</span>
              <Input
                value={metricConfig.suffix}
                onChange={(e) =>
                  setMetricConfig({ ...metricConfig, suffix: e.target.value })
                }
                onBlur={() => persist({ config_json: metricConfig })}
              />
            </label>
          </>
        )}

        {tab === "display" && widget.widget_type === "bar_chart" && (
          <>
            {schemaColumns.length > 0 && (
              <label className="block space-y-1">
                <span className="text-xs text-zinc-500">X axis (category)</span>
                <select
                  className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                  value={barChartConfig.x_axis ?? ""}
                  onChange={(e) => {
                    const next = {
                      ...barChartConfig,
                      x_axis: e.target.value || null,
                    };
                    setBarChartConfig(next);
                    persist({ config_json: next });
                  }}
                >
                  <option value="">—</option>
                  {schemaColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Aggregation</span>
              <select
                className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                value={barChartConfig.aggregation}
                onChange={(e) => {
                  const next = {
                    ...barChartConfig,
                    aggregation: e.target.value as MetricAggregation,
                  };
                  setBarChartConfig(next);
                  persist({ config_json: next });
                }}
              >
                {AGGREGATIONS.map((agg) => (
                  <option key={agg} value={agg}>
                    {agg}
                  </option>
                ))}
              </select>
            </label>
            {schemaColumns.length > 0 && (
              <label className="block space-y-1">
                <span className="text-xs text-zinc-500">
                  Y axis (value){columnRequired ? "" : " (optional for count)"}
                </span>
                <select
                  className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                  value={barChartConfig.y_axis ?? ""}
                  onChange={(e) => {
                    const next = {
                      ...barChartConfig,
                      y_axis: e.target.value || null,
                    };
                    setBarChartConfig(next);
                    persist({ config_json: next });
                  }}
                >
                  <option value="">—</option>
                  {schemaColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </>
        )}

        {tab === "display" && widget.widget_type === "filter" && (
          <>
            <label className="block space-y-1">
              <span className="text-xs text-zinc-500">Label</span>
              <Input
                value={filterConfig.label ?? ""}
                onChange={(e) =>
                  setFilterConfig({ ...filterConfig, label: e.target.value || null })
                }
                onBlur={() => persist({ config_json: filterConfig })}
              />
            </label>
            {schemaColumns.length > 0 && (
              <label className="block space-y-1">
                <span className="text-xs text-zinc-500">Source column</span>
                <select
                  className="h-9 w-full border border-zinc-600 bg-zinc-950 px-3 text-sm text-zinc-100"
                  value={filterConfig.source_column ?? ""}
                  onChange={(e) => {
                    const next = {
                      ...filterConfig,
                      source_column: e.target.value || null,
                    };
                    setFilterConfig(next);
                    persist({ config_json: next });
                  }}
                >
                  <option value="">—</option>
                  {schemaColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="flex items-center gap-2 text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={filterConfig.multi_select}
                onChange={(e) => {
                  const next = { ...filterConfig, multi_select: e.target.checked };
                  setFilterConfig(next);
                  persist({ config_json: next });
                }}
              />
              <span>Allow multi-select</span>
            </label>
            {targetWidgets.length > 0 && (
              <fieldset className="space-y-2">
                <legend className="text-xs text-zinc-500">Applies to</legend>
                <div className="max-h-40 space-y-1 overflow-auto">
                  {targetWidgets.map((target) => (
                    <label
                      key={target.id}
                      className="flex items-center gap-2 text-xs text-zinc-300"
                    >
                      <input
                        type="checkbox"
                        checked={filterConfig.applies_to.includes(target.id)}
                        onChange={(e) => {
                          const appliesTo = e.target.checked
                            ? [...filterConfig.applies_to, target.id]
                            : filterConfig.applies_to.filter((id) => id !== target.id);
                          const next = { ...filterConfig, applies_to: appliesTo };
                          setFilterConfig(next);
                          persist({ config_json: next });
                        }}
                      />
                      <span>
                        {target.title ?? target.widget_type} ({target.widget_type})
                      </span>
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
          </>
        )}

        {tab === "display" && widget.widget_type === "text" && (
          <label className="block space-y-1">
            <span className="text-xs text-zinc-500">Markdown content</span>
            <textarea
              className="min-h-[160px] w-full border border-zinc-600 bg-zinc-950 px-3 py-2 font-data text-xs text-zinc-100"
              rows={8}
              value={textConfig.content}
              onChange={(e) => setTextConfig({ ...textConfig, content: e.target.value })}
              onBlur={(e) => {
                const next = { ...textConfig, content: e.target.value };
                setTextConfig(next);
                persist({ config_json: next });
              }}
              placeholder={"# Title\n- item one\n**bold**"}
            />
          </label>
        )}

        {saveError && <p className="text-xs text-red-400">{saveError}</p>}
        {updateWidget.isPending && (
          <p className="text-xs text-zinc-500">Saving…</p>
        )}
      </div>
    </aside>
  );
}
