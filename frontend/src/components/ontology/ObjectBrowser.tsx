import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";

export function ObjectBrowser({
  columns,
  rows,
  loading,
  error,
  page,
  totalPages,
  onPageChange,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
  loading?: boolean;
  error?: string | null;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-600 bg-red-950/30 p-4 text-sm text-red-300">
        {error}
      </div>
    );
  }

  if (!rows.length) {
    return <p className="text-sm text-zinc-500">No objects found.</p>;
  }

  return (
    <div>
      <div className="overflow-x-auto border border-zinc-700">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-700 bg-zinc-900 text-xs text-zinc-500">
              {columns.map((col) => (
                <th key={col} className="px-3 py-2 font-data">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-zinc-800 font-data">
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2">
                    {String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <span className="text-xs text-zinc-500">
          Page {page} of {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
