import { BarChart3, Filter, Gauge, Table2, Type } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function WidgetPalette({
  widgetCount,
  onAddTable,
  onAddMetric,
  onAddBarChart,
  onAddFilter,
  onAddText,
  adding,
}: {
  widgetCount: number;
  onAddTable: () => void;
  onAddMetric: () => void;
  onAddBarChart: () => void;
  onAddFilter: () => void;
  onAddText: () => void;
  adding: boolean;
}) {
  return (
    <aside className="border border-zinc-700 bg-zinc-900 p-3">
      <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">Widgets</h2>
      <div className="space-y-2">
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
          disabled={adding}
          onClick={onAddTable}
        >
          <Table2 className="h-4 w-4" />
          Table
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
          disabled={adding}
          onClick={onAddMetric}
        >
          <Gauge className="h-4 w-4" />
          Metric
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
          disabled={adding}
          onClick={onAddBarChart}
        >
          <BarChart3 className="h-4 w-4" />
          Bar Chart
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
          disabled={adding}
          onClick={onAddFilter}
        >
          <Filter className="h-4 w-4" />
          Filter
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start gap-2"
          disabled={adding}
          onClick={onAddText}
        >
          <Type className="h-4 w-4" />
          Text
        </Button>
      </div>
      <p className="mt-3 text-xs text-zinc-500">{widgetCount} on dashboard</p>
    </aside>
  );
}
