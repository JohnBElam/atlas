import { Link } from "@tanstack/react-router";
import type { Dataset } from "@/types/dataset";

export function DatasetCard({ dataset }: { dataset: Dataset }) {
  return (
    <Link
      to="/datasets/$id"
      params={{ id: dataset.id }}
      className="block border border-zinc-700 bg-zinc-900 p-4 hover:border-indigo-600"
    >
      <h3 className="font-medium text-zinc-100">{dataset.display_name}</h3>
      <p className="mt-1 font-data text-xs text-zinc-500">{dataset.name}</p>
      {dataset.row_count != null && (
        <p className="mt-2 text-xs text-zinc-400">{dataset.row_count.toLocaleString()} rows</p>
      )}
    </Link>
  );
}
