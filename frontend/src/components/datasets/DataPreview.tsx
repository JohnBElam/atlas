import { Skeleton } from "@/components/ui/Skeleton";
import type { DatasetPreview } from "@/types/dataset";

export function DataPreview({
  preview,
  loading,
  error,
}: {
  preview?: DatasetPreview | null;
  loading?: boolean;
  error?: string | null;
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-400">{error}</p>;
  }

  if (!preview || !preview.rows.length) {
    return <p className="text-sm text-zinc-500">No rows to display.</p>;
  }

  return (
    <div className="overflow-x-auto border border-zinc-700">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-700 bg-zinc-900 text-xs text-zinc-500">
            {preview.columns.map((col) => (
              <th key={col} className="px-3 py-2 font-data">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.rows.map((row, i) => (
            <tr key={i} className="border-b border-zinc-800 font-data">
              {preview.columns.map((col) => (
                <td key={col} className="px-3 py-2 text-zinc-300">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
