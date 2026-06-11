import { Link } from "@tanstack/react-router";
import { Badge } from "@/components/ui/Badge";
import type { Source } from "@/types/source";

export function SourceCard({ source }: { source: Source }) {
  return (
    <Link
      to="/sources/$id"
      params={{ id: source.id }}
      className="block border border-zinc-700 bg-zinc-900 p-4 transition-colors hover:border-indigo-600"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-medium text-zinc-100">{source.name}</h3>
          <p className="mt-1 text-xs text-zinc-500 font-data">{source.source_type}</p>
        </div>
        <Badge variant={source.is_active ? "success" : "warning"}>
          {source.is_active ? "Active" : "Inactive"}
        </Badge>
      </div>
      {source.schema_discovered_at && (
        <p className="mt-3 text-xs text-zinc-500">
          Schema discovered {new Date(source.schema_discovered_at).toLocaleString()}
        </p>
      )}
    </Link>
  );
}
