import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import { Link } from "@tanstack/react-router";
import { useCreateWidget, useDashboard, useUpdateDashboard } from "@/api/analytics";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardCanvas } from "@/components/workshop/DashboardCanvas";
import { WidgetConfigPanel } from "@/components/workshop/WidgetConfigPanel";
import { WidgetPalette } from "@/components/workshop/WidgetPalette";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { useWorkshopStore } from "@/stores/workshop-store";
import type { LayoutItem, Widget } from "@/types/analytics";

function nextLayoutPosition(layout: LayoutItem[]): { x: number; y: number } {
  if (layout.length === 0) {
    return { x: 0, y: 0 };
  }
  const maxY = Math.max(...layout.map((item) => item.y + item.h));
  return { x: 0, y: maxY };
}

function addWidgetToLayout(
  setLayout: Dispatch<SetStateAction<LayoutItem[]>>,
  widget: Widget,
  size: { w: number; h: number },
  setSelectedWidgetId: (id: string) => void,
  setLayoutDirty: (dirty: boolean) => void,
) {
  if (!widget?.id) return;
  setLayoutDirty(true);
  setSelectedWidgetId(widget.id);
  setLayout((current) => {
    const pos = nextLayoutPosition(current);
    return [...current, { widget_id: widget.id, x: pos.x, y: pos.y, ...size }];
  });
}

export function DashboardBuilderPage({ id }: { id: string }) {
  const { data, isLoading, isError, error } = useDashboard(id);
  const updateDashboard = useUpdateDashboard(id);
  const createWidget = useCreateWidget(id);
  const selectedWidgetId = useWorkshopStore((s) => s.selectedWidgetId);
  const setSelectedWidgetId = useWorkshopStore((s) => s.setSelectedWidgetId);
  const setBuilderMode = useWorkshopStore((s) => s.setBuilderMode);

  const [name, setName] = useState("");
  const [layout, setLayout] = useState<LayoutItem[]>([]);
  const [layoutDirty, setLayoutDirty] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    setBuilderMode("edit");
    return () => setSelectedWidgetId(null);
  }, [setBuilderMode, setSelectedWidgetId]);

  useEffect(() => {
    if (data?.dashboard && !layoutDirty) {
      setName(data.dashboard.name);
      setLayout(data.dashboard.layout_json);
    }
  }, [data, layoutDirty]);

  const widgetsById = useMemo(() => {
    const map = new Map<string, Widget>();
    for (const widget of data?.widgets ?? []) {
      map.set(widget.id, widget);
    }
    return map;
  }, [data?.widgets]);

  const selectedWidget = selectedWidgetId
    ? widgetsById.get(selectedWidgetId) ?? null
    : null;

  const createAndPlace = (
    body: Parameters<typeof createWidget.mutate>[0],
    size: { w: number; h: number },
  ) => {
    setActionError(null);
    setSaveSuccess(false);
    createWidget.mutate(body, {
      onSuccess: (widget) => {
        if (widget) {
          addWidgetToLayout(setLayout, widget, size, setSelectedWidgetId, setLayoutDirty);
        }
      },
      onError: (err) => setActionError(getErrorMessage(err)),
    });
  };

  if (isLoading) {
    return (
      <AppShell title="Dashboard Builder">
        <Skeleton className="h-[500px]" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Dashboard Builder">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!data?.dashboard) {
    return (
      <AppShell title="Dashboard Builder">
        <p className="text-red-400">Dashboard not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={`Builder · ${data.dashboard.name}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link to="/workshop" className="text-sm text-indigo-400 hover:text-indigo-300">
          ← All dashboards
        </Link>
        <div className="flex items-center gap-3">
          {saveSuccess && <span className="text-sm text-emerald-400">Saved</span>}
          <Link
            to="/workshop/$id/view"
            params={{ id }}
            className="text-sm text-zinc-400 hover:text-zinc-200"
          >
            Preview
          </Link>
          <Button
            disabled={updateDashboard.isPending}
            onClick={() => {
              setSaveError(null);
              setSaveSuccess(false);
              updateDashboard.mutate(
                { name, layout_json: layout },
                {
                  onSuccess: () => {
                    setLayoutDirty(false);
                    setSaveSuccess(true);
                  },
                  onError: (err) => setSaveError(getErrorMessage(err)),
                },
              );
            }}
          >
            Save
          </Button>
        </div>
      </div>

      <div className="mb-4 max-w-md">
        <Input
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setLayoutDirty(true);
            setSaveSuccess(false);
          }}
          placeholder="Dashboard name"
        />
      </div>

      {(saveError || actionError) && (
        <div className="mb-4">
          <ErrorMessage message={saveError ?? actionError ?? ""} />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[240px_1fr_320px]">
        <WidgetPalette
          widgetCount={data.widgets.length}
          onAddTable={() =>
            createAndPlace(
              {
                widget_type: "table",
                title: `Table ${data.widgets.length + 1}`,
                config_json: { page_size: 50 },
                data_binding_json: null,
              },
              { w: 6, h: 4 },
            )
          }
          onAddMetric={() =>
            createAndPlace(
              {
                widget_type: "metric_card",
                title: `Metric ${data.widgets.length + 1}`,
                config_json: { aggregation: "count", format: "number" },
                data_binding_json: null,
              },
              { w: 3, h: 2 },
            )
          }
          onAddBarChart={() =>
            createAndPlace(
              {
                widget_type: "bar_chart",
                title: `Bar Chart ${data.widgets.length + 1}`,
                config_json: { aggregation: "sum" },
                data_binding_json: null,
              },
              { w: 6, h: 4 },
            )
          }
          onAddFilter={() =>
            createAndPlace(
              {
                widget_type: "filter",
                title: `Filter ${data.widgets.length + 1}`,
                config_json: { filter_type: "dropdown" },
                data_binding_json: null,
              },
              { w: 3, h: 2 },
            )
          }
          onAddText={() =>
            createAndPlace(
              {
                widget_type: "text",
                title: `Text ${data.widgets.length + 1}`,
                config_json: { content: "" },
                data_binding_json: null,
              },
              { w: 4, h: 3 },
            )
          }
          adding={createWidget.isPending}
        />

        <DashboardCanvas
          layout={layout}
          widgets={data.widgets}
          selectedWidgetId={selectedWidgetId}
          onSelect={setSelectedWidgetId}
          onLayoutChange={(next) => {
            setLayout(next);
            setLayoutDirty(true);
            setSaveSuccess(false);
          }}
        />

        <WidgetConfigPanel
          dashboardId={id}
          widget={selectedWidget}
          widgets={data.widgets}
        />
      </div>
    </AppShell>
  );
}
