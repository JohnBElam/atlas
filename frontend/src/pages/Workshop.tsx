import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useCreateDashboard, useDashboards } from "@/api/analytics";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";
import type { Dashboard } from "@/types/analytics";

function DashboardCard({ dashboard }: { dashboard: Dashboard }) {
  const widgetCount = dashboard.layout_json.length;
  return (
    <Link
      to="/workshop/$id/edit"
      params={{ id: dashboard.id }}
      className="block border border-zinc-700 bg-zinc-900 p-4 hover:border-indigo-600"
    >
      <h3 className="font-medium text-zinc-100">{dashboard.name}</h3>
      {dashboard.description && (
        <p className="mt-1 text-sm text-zinc-500">{dashboard.description}</p>
      )}
      <p className="mt-2 text-xs text-zinc-400">
        {widgetCount} {widgetCount === 1 ? "widget" : "widgets"} on canvas
      </p>
    </Link>
  );
}

export function WorkshopPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useDashboards();
  const createDashboard = useCreateDashboard();
  const [name, setName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  return (
    <AppShell title="Workshop">
      <form
        className="mb-6 max-w-md space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          setCreateError(null);
          createDashboard.mutate(
            { name },
            {
              onSuccess: (dashboard) => {
                setName("");
                if (dashboard?.id) {
                  void navigate({
                    to: "/workshop/$id/edit",
                    params: { id: dashboard.id },
                  });
                }
              },
              onError: (err) => setCreateError(getErrorMessage(err)),
            },
          );
        }}
      >
        <div className="flex gap-3">
          <Input
            placeholder="Dashboard name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Button type="submit" disabled={!name || createDashboard.isPending}>
            Create
          </Button>
        </div>
        {createError && <ErrorMessage message={createError} />}
      </form>

      {isLoading ? (
        <Skeleton className="h-28 w-full max-w-sm" />
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.map((dashboard) => (
            <DashboardCard key={dashboard.id} dashboard={dashboard} />
          ))}
          {!data?.length && (
            <p className="text-sm text-zinc-500">
              No dashboards yet. Create one to open the builder.
            </p>
          )}
        </div>
      )}
    </AppShell>
  );
}
