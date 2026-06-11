import { Link } from "@tanstack/react-router";
import { buttonClassName } from "@/components/ui/Button";
import { RunStatusBadge } from "@/components/pipelines/RunStatusBadge";
import { useDatasetSnapshots } from "@/api/lineage";
import type { LineageNodeData } from "@/types/lineage";

export function LineageDetailPanel({ node }: { node: LineageNodeData | null }) {
  const datasetId = node?.node_type === "dataset" ? node.entity_id : "";
  const { data: snapshots } = useDatasetSnapshots(datasetId);

  if (!node) {
    return <p className="text-sm text-zinc-500">Select a node to view details.</p>;
  }

  return (
    <div className="space-y-3 border border-zinc-700 bg-zinc-900 p-4">
      <h3 className="font-medium text-zinc-100">{node.label}</h3>
      <p className="text-xs capitalize text-zinc-500">{node.node_type}</p>
      {node.row_count != null && (
        <p className="text-sm text-zinc-400">{node.row_count.toLocaleString()} rows</p>
      )}
      {node.connector_type && (
        <p className="font-data text-sm text-zinc-400">{node.connector_type}</p>
      )}
      {node.last_run_status && <RunStatusBadge status={node.last_run_status} />}
      {node.last_updated && (
        <p className="text-xs text-zinc-500">
          Updated {new Date(node.last_updated).toLocaleString()}
        </p>
      )}

      {node.node_type === "pipeline" && (
        <Link
          to="/pipelines/$id"
          params={{ id: node.entity_id }}
          className={buttonClassName({ variant: "outline", size: "sm" })}
        >
          View Pipeline
        </Link>
      )}
      {node.node_type === "dataset" && (
        <>
          <Link
            to="/datasets/$id"
            params={{ id: node.entity_id }}
            className={buttonClassName({ variant: "outline", size: "sm" })}
          >
            View Dataset
          </Link>
          <Link
            to="/lineage/dataset/$id"
            params={{ id: node.entity_id }}
            className={buttonClassName({ variant: "ghost", size: "sm", className: "w-full" })}
          >
            Focus subgraph
          </Link>
          {snapshots && snapshots.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-medium text-zinc-400">Recent snapshots</h4>
              <ul className="space-y-1 text-xs text-zinc-500">
                {snapshots.slice(0, 5).map((snap) => (
                  <li key={snap.snapshot_id} className="font-data">
                    #{snap.snapshot_id}
                    {snap.summary ? ` · ${snap.summary}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
