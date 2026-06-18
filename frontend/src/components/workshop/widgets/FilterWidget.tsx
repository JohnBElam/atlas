import { useEffect } from "react";
import { useWidgetData } from "@/api/analytics";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { useWorkshopStore } from "@/stores/workshop-store";
import {
  parseDataBinding,
  parseFilterConfig,
  type Widget,
} from "@/types/analytics";

export function FilterWidget({
  widget,
  onError,
}: {
  widget: Widget;
  onError?: (message: string | null) => void;
}) {
  const binding = parseDataBinding(widget.data_binding_json);
  const config = parseFilterConfig(widget.config_json);
  const hasBinding = binding?.source_type === "dataset" && !!binding.dataset_id;
  const hasColumn = !!config.source_column;
  const filterValue = useWorkshopStore((s) => s.filterState[widget.id]);
  const setFilterValue = useWorkshopStore((s) => s.setFilterValue);

  const { data, isLoading, isError, error } = useWidgetData(
    widget.id,
    {},
    hasBinding && hasColumn,
  );

  useEffect(() => {
    onError?.(isError ? getErrorMessage(error) : null);
  }, [isError, error, onError]);

  if (!hasBinding) {
    return <p className="text-xs text-zinc-500">Select a dataset in Data Binding.</p>;
  }

  if (!hasColumn) {
    return <p className="text-xs text-zinc-500">Configure source column in Display.</p>;
  }

  if (isLoading) {
    return <Skeleton className="h-8 w-full" />;
  }

  if (isError) {
    return <p className="text-xs text-red-400">{getErrorMessage(error)}</p>;
  }

  const options = (data?.rows ?? [])
    .map((row) => String(row.value ?? ""))
    .filter((value) => value.length > 0);

  if (options.length === 0) {
    return <p className="text-xs text-zinc-500">No filter values available.</p>;
  }

  const displayLabel = config.label ?? widget.title ?? "Filter";

  if (config.multi_select) {
    const selected = Array.isArray(filterValue) ? filterValue : [];
    return (
      <div className="space-y-1">
        <span className="text-xs text-zinc-500">{displayLabel}</span>
        <div className="max-h-32 space-y-1 overflow-auto">
          {options.map((option) => (
            <label key={option} className="flex items-center gap-2 text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...selected, option]
                    : selected.filter((v) => v !== option);
                  setFilterValue(widget.id, next);
                }}
              />
              <span className="font-data">{option}</span>
            </label>
          ))}
        </div>
      </div>
    );
  }

  return (
    <label className="block space-y-1">
      <span className="text-xs text-zinc-500">{displayLabel}</span>
      <select
        className="h-8 w-full border border-zinc-600 bg-zinc-950 px-2 text-xs text-zinc-100"
        value={typeof filterValue === "string" ? filterValue : ""}
        onChange={(e) => setFilterValue(widget.id, e.target.value)}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
