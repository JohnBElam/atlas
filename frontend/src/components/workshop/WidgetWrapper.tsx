import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { useWorkshopStore } from "@/stores/workshop-store";
import {
  buildApplicableFilters,
  type LayoutItem,
  type Widget,
} from "@/types/analytics";
import { TableWidget } from "@/components/workshop/widgets/TableWidget";
import { MetricWidget } from "@/components/workshop/widgets/MetricWidget";
import { BarChartWidget } from "@/components/workshop/widgets/BarChartWidget";
import { FilterWidget } from "@/components/workshop/widgets/FilterWidget";
import { TextWidget } from "@/components/workshop/widgets/TextWidget";

export const WORKSHOP_CELL_PX = 80;
export const WORKSHOP_COLS = 12;

export function WidgetWrapper({
  widget,
  layout,
  allWidgets,
  selected,
  readOnly = false,
  dragHandleProps,
  onSelect,
}: {
  widget: Widget;
  layout: LayoutItem;
  allWidgets: Widget[];
  selected: boolean;
  readOnly?: boolean;
  dragHandleProps?: Record<string, unknown>;
  onSelect: (widgetId: string) => void;
}) {
  const [dataError, setDataError] = useState<string | null>(null);
  const filterState = useWorkshopStore((s) => s.filterState);

  const applicableFilters = useMemo(
    () => buildApplicableFilters(widget.id, allWidgets, filterState),
    [widget.id, allWidgets, filterState],
  );

  return (
    <div
      className={cn(
        "absolute flex flex-col overflow-hidden bg-zinc-900",
        selected && !readOnly ? "border-2 border-indigo-500" : "border border-zinc-600",
        dataError && "border-red-500",
      )}
      style={
        layout.x === 0 && layout.y === 0
          ? { inset: 0, width: "100%", height: "100%" }
          : {
              left: layout.x * WORKSHOP_CELL_PX,
              top: layout.y * WORKSHOP_CELL_PX,
              width: layout.w * WORKSHOP_CELL_PX,
              height: layout.h * WORKSHOP_CELL_PX,
            }
      }
      onClick={(e) => {
        if (readOnly) return;
        e.stopPropagation();
        onSelect(widget.id);
      }}
      onKeyDown={(e) => {
        if (readOnly) return;
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(widget.id);
        }
      }}
      role={readOnly ? undefined : "button"}
      tabIndex={readOnly ? undefined : 0}
    >
      <div
        className={cn(
          "flex shrink-0 items-center justify-between border-b border-zinc-700 px-2 py-1",
          !readOnly && dragHandleProps && "cursor-grab active:cursor-grabbing",
        )}
        {...(readOnly ? {} : dragHandleProps)}
      >
        <span className="truncate text-xs font-medium text-zinc-300">
          {widget.title ?? "Untitled widget"}
        </span>
        <span className="text-[10px] uppercase text-zinc-500">{widget.widget_type}</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-2">
        {widget.widget_type === "table" && (
          <TableWidget widget={widget} filters={applicableFilters} onError={setDataError} />
        )}
        {widget.widget_type === "metric_card" && (
          <MetricWidget widget={widget} filters={applicableFilters} onError={setDataError} />
        )}
        {widget.widget_type === "bar_chart" && (
          <BarChartWidget widget={widget} filters={applicableFilters} onError={setDataError} />
        )}
        {widget.widget_type === "filter" && (
          <FilterWidget widget={widget} onError={setDataError} />
        )}
        {widget.widget_type === "text" && <TextWidget widget={widget} />}
      </div>
      {dataError && (
        <p className="shrink-0 border-t border-red-900/50 bg-red-950/30 px-2 py-1 text-[10px] text-red-400">
          {dataError}
        </p>
      )}
    </div>
  );
}
