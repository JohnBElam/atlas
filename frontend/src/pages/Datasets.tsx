import { Link } from "@tanstack/react-router";
import { useDatasets } from "@/api/datasets";
import { AppShell } from "@/components/layout/AppShell";
import { DatasetCard } from "@/components/datasets/DatasetCard";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function DatasetsPage() {
  const { data, isLoading, isError, error } = useDatasets();

  return (
    <AppShell title="Datasets">
      <p className="mb-6 text-sm text-zinc-400">
        Datasets are platform-owned Iceberg tables. Ingest from a{" "}
        <Link to="/sources" className="text-indigo-400 hover:text-indigo-300">
          Source
        </Link>{" "}
        to create one, or run a pipeline with an Output node to publish a transformed table.
      </p>
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.map((dataset) => <DatasetCard key={dataset.id} dataset={dataset} />)}
          {!data?.length && <p className="text-sm text-zinc-500">No datasets yet.</p>}
        </div>
      )}
    </AppShell>
  );
}
