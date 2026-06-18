import { useEffect } from "react";
import { useWidgetData } from "@/api/analytics";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import {
  formatMetricValue,
  parseDataBinding,
  parseMetricConfig,
  type Widget,
  type WidgetFilterState,
} from "@/types/analytics";

export function MetricWidget({
  widget,
  filters = {},
  onError,
}: {
  widget: Widget;
  filters?: WidgetFilterState;
  onError?: (message: string | null) => void;
}) {
  const binding = parseDataBinding(widget.data_binding_json);
  const config = parseMetricConfig(widget.config_json);
  const hasBinding = binding?.source_type === "dataset" && !!binding.dataset_id;
  const { data, isLoading, isError, error } = useWidgetData(widget.id, filters, hasBinding);

  useEffect(() => {
    onError?.(isError ? getErrorMessage(error) : null);
  }, [isError, error, onError]);

  if (!hasBinding) {
    return <p className="text-xs text-zinc-500">Select a dataset in Data Binding.</p>;
  }

  if (isLoading) {
    return <Skeleton className="h-12 w-full" />;
  }

  if (isError) {
    return <p className="text-xs text-red-400">{getErrorMessage(error)}</p>;
  }

  const rawValue = data?.rows[0]?.value;
  if (rawValue === null || rawValue === undefined) {
    return <p className="text-xs text-zinc-500">No value to display.</p>;
  }

  const displayLabel = config.label ?? widget.title ?? "Metric";

  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <p className="text-xs uppercase tracking-wide text-zinc-500">{displayLabel}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-100">
        {formatMetricValue(rawValue, config)}
      </p>
    </div>
  );
}
