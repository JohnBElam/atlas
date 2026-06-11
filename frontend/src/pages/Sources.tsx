import { useState } from "react";
import { useCreateSource, useSources } from "@/api/sources";
import { AppShell } from "@/components/layout/AppShell";
import { SourceCard } from "@/components/sources/SourceCard";
import { SourceForm } from "@/components/sources/SourceForm";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function SourcesPage() {
  const { data, isLoading, isError, error } = useSources();
  const createSource = useCreateSource();
  const [showForm, setShowForm] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  return (
    <AppShell title="Sources">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-zinc-400">Register and manage data sources.</p>
        <button
          className="text-sm text-indigo-400 hover:text-indigo-300"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "Hide form" : "New source"}
        </button>
      </div>
      {showForm && (
        <div className="mb-6 max-w-md space-y-3">
          <SourceForm
            loading={createSource.isPending}
            onSubmit={(values) => {
              setCreateError(null);
              createSource.mutate(values, {
                onSuccess: () => {
                  setShowForm(false);
                  setCreateError(null);
                },
                onError: (err) => setCreateError(getErrorMessage(err)),
              });
            }}
          />
          {createError && <ErrorMessage message={createError} />}
        </div>
      )}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.map((source) => <SourceCard key={source.id} source={source} />)}
          {!data?.length && <p className="text-sm text-zinc-500">No sources yet.</p>}
        </div>
      )}
    </AppShell>
  );
}
