import { useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { useDashboard } from "@/api/analytics";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardCanvas } from "@/components/workshop/DashboardCanvas";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import { useWorkshopStore } from "@/stores/workshop-store";

export function DashboardViewerPage({ id }: { id: string }) {
  const { data, isLoading, isError, error } = useDashboard(id);
  const setBuilderMode = useWorkshopStore((s) => s.setBuilderMode);
  const setSelectedWidgetId = useWorkshopStore((s) => s.setSelectedWidgetId);

  useEffect(() => {
    setBuilderMode("view");
    setSelectedWidgetId(null);
    return () => setBuilderMode("edit");
  }, [setBuilderMode, setSelectedWidgetId]);

  if (isLoading) {
    return (
      <AppShell title="Dashboard Viewer">
        <Skeleton className="h-[500px]" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Dashboard Viewer">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!data?.dashboard) {
    return (
      <AppShell title="Dashboard Viewer">
        <p className="text-red-400">Dashboard not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={`View · ${data.dashboard.name}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link to="/workshop" className="text-sm text-indigo-400 hover:text-indigo-300">
          ← All dashboards
        </Link>
        <Link
          to="/workshop/$id/edit"
          params={{ id }}
          className="text-sm text-zinc-400 hover:text-zinc-200"
        >
          Edit
        </Link>
      </div>

      <DashboardCanvas
        layout={data.dashboard.layout_json}
        widgets={data.widgets}
        readOnly
        selectedWidgetId={null}
        onSelect={() => undefined}
        onLayoutChange={() => undefined}
      />
    </AppShell>
  );
}
