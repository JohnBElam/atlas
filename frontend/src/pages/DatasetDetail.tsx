import { Link } from "@tanstack/react-router";
import { useDataset, useDatasetPreview, useDatasetProfile } from "@/api/datasets";
import { AppShell } from "@/components/layout/AppShell";
import { DataPreview } from "@/components/datasets/DataPreview";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { getErrorMessage } from "@/lib/errors";

export function DatasetDetailPage({ id }: { id: string }) {
  const { data: dataset, isLoading, isError, error } = useDataset(id);
  const { data: preview, isLoading: previewLoading, isError: previewError, error: previewErr } =
    useDatasetPreview(id);
  const { data: profile, isLoading: profileLoading, isError: profileIsError, error: profileErr } =
    useDatasetProfile(id);

  if (isLoading) {
    return (
      <AppShell title="Dataset">
        <Skeleton className="h-40" />
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell title="Dataset">
        <ErrorMessage message={getErrorMessage(error)} />
      </AppShell>
    );
  }

  if (!dataset) {
    return (
      <AppShell title="Dataset">
        <p className="text-red-400">Dataset not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={dataset.display_name}>
      <div className="space-y-8">
        <div className="text-sm text-zinc-400">
          <span className="font-data">{dataset.iceberg_namespace}.{dataset.iceberg_table}</span>
          {dataset.row_count != null && (
            <span className="ml-4">{dataset.row_count.toLocaleString()} rows</span>
          )}
          <Link
            to="/lineage/dataset/$id"
            params={{ id }}
            className="ml-4 text-indigo-400 hover:text-indigo-300"
          >
            View lineage
          </Link>
        </div>

        <section>
          <h2 className="mb-3 text-sm font-medium">Preview</h2>
          <DataPreview
            preview={preview}
            loading={previewLoading}
            error={previewError ? getErrorMessage(previewErr) : null}
          />
        </section>

        <section>
          <h2 className="mb-3 text-sm font-medium">Profile</h2>
          {profileLoading ? (
            <Skeleton className="h-32" />
          ) : profileIsError ? (
            <ErrorMessage message={getErrorMessage(profileErr)} />
          ) : profile ? (
            <div className="overflow-x-auto border border-zinc-700">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-700 text-xs text-zinc-500">
                    <th className="px-3 py-2">Column</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Distinct</th>
                    <th className="px-3 py-2">Nulls</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.columns.map((col) => (
                    <tr key={col.name} className="border-b border-zinc-800 font-data">
                      <td className="px-3 py-2">{col.name}</td>
                      <td className="px-3 py-2 text-zinc-400">{col.type}</td>
                      <td className="px-3 py-2">{col.distinct_count ?? "—"}</td>
                      <td className="px-3 py-2">{col.null_count ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
