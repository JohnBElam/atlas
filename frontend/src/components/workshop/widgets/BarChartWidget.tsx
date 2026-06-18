import { useEffect, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useWidgetData } from "@/api/analytics";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { parseBarChartConfig, parseDataBinding, type Widget, type WidgetFilterState } from "@/types/analytics";

export function BarChartWidget({
  widget,
  filters = {},
  onError,
}: {
  widget: Widget;
  filters?: WidgetFilterState;
  onError?: (message: string | null) => void;
}) {
  const binding = parseDataBinding(widget.data_binding_json);
  const config = parseBarChartConfig(widget.config_json);
  const hasBinding = binding?.source_type === "dataset" && !!binding.dataset_id;
  const hasAxes = !!config.x_axis && (config.aggregation === "count" || !!config.y_axis);
  const { data, isLoading, isError, error } = useWidgetData(
    widget.id,
    filters,
    hasBinding && hasAxes,
  );

  useEffect(() => {
    onError?.(isError ? getErrorMessage(error) : null);
  }, [isError, error, onError]);

  const chartData = useMemo(
    () =>
      (data?.rows ?? []).map((row) => ({
        name: String(row.category ?? ""),
        value: Number(row.value ?? 0),
      })),
    [data?.rows],
  );

  if (!hasBinding) {
    return <p className="text-xs text-zinc-500">Select a dataset in Data Binding.</p>;
  }

  if (!hasAxes) {
    return <p className="text-xs text-zinc-500">Configure x-axis and y-axis in Display.</p>;
  }

  if (isLoading) {
    return <Skeleton className="h-full w-full min-h-[120px]" />;
  }

  if (isError) {
    return <p className="text-xs text-red-400">{getErrorMessage(error)}</p>;
  }

  if (chartData.length === 0) {
    return <p className="text-xs text-zinc-500">No data to display.</p>;
  }

  const valueLabel = config.y_axis
    ? `${config.aggregation}(${config.y_axis})`
    : config.aggregation;

  return (
    <div className="h-full min-h-[120px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
        <XAxis
          dataKey="name"
          tick={{ fill: "#a1a1aa", fontSize: 10 }}
          axisLine={{ stroke: "#52525b" }}
          tickLine={{ stroke: "#52525b" }}
        />
        <YAxis
          tick={{ fill: "#a1a1aa", fontSize: 10 }}
          axisLine={{ stroke: "#52525b" }}
          tickLine={{ stroke: "#52525b" }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#18181b",
            border: "1px solid #52525b",
            borderRadius: 0,
          }}
          labelStyle={{ color: "#e4e4e7" }}
          itemStyle={{ color: "#a5b4fc" }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "#a1a1aa" }} />
        <Bar dataKey="value" name={valueLabel} fill="#6366f1" />
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}
