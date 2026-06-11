import { Link } from "@tanstack/react-router";
import { Input } from "@/components/ui/Input";
import { useDatasets } from "@/api/datasets";
import type { PipelineDag } from "@/types/pipeline";

export function NodeConfigPanel({
  dag,
  selectedNodeId,
  onChange,
}: {
  dag: PipelineDag;
  selectedNodeId: string | null;
  onChange: (dag: PipelineDag) => void;
}) {
  const { data: datasets, isLoading } = useDatasets();
  const node = dag.nodes.find((n) => n.id === selectedNodeId);

  if (!node) {
    return <p className="text-sm text-zinc-500">Select a node to configure.</p>;
  }

  const updateNode = (patch: Record<string, unknown>) => {
    onChange({
      ...dag,
      nodes: dag.nodes.map((n) => (n.id === node.id ? { ...n, ...patch } : n)),
    });
  };

  if (node.type === "source") {
    return (
      <div className="space-y-3 border border-zinc-700 bg-zinc-900 p-4">
        <h3 className="text-sm font-medium">Input dataset</h3>
        <p className="text-xs text-zinc-500">
          Pipeline inputs read from ingested datasets (Iceberg tables), not directly from
          sources. Ingest a source first, then pick it here.
        </p>
        <label className="block text-xs text-zinc-400">Dataset</label>
        {isLoading ? (
          <p className="text-xs text-zinc-500">Loading datasets…</p>
        ) : !datasets?.length ? (
          <div className="space-y-2 text-xs text-zinc-500">
            <p>No datasets yet.</p>
            <ol className="list-inside list-decimal space-y-1">
              <li>
                Open a{" "}
                <Link to="/sources" className="text-indigo-400 hover:text-indigo-300">
                  Source
                </Link>{" "}
                and upload a file
              </li>
              <li>Use &quot;Ingest to dataset&quot; on the source detail page</li>
              <li>Return here and select the new dataset</li>
            </ol>
          </div>
        ) : (
          <select
            className="h-9 w-full rounded-sm border border-zinc-600 bg-zinc-900 px-3 text-sm"
            value={node.dataset_id ?? ""}
            onChange={(e) => updateNode({ dataset_id: e.target.value })}
          >
            <option value="">Select dataset</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.display_name}
              </option>
            ))}
          </select>
        )}
      </div>
    );
  }

  if (node.type === "transform" && node.transform_type === "filter") {
    const conditions = (node.config?.conditions as { column: string; operator: string; value: string }[]) ?? [];
    const first = conditions[0] ?? { column: "", operator: "eq", value: "" };
    return (
      <div className="space-y-3 border border-zinc-700 bg-zinc-900 p-4">
        <h3 className="text-sm font-medium">Filter config</h3>
        <label className="block text-xs text-zinc-400">Column</label>
        <Input
          value={first.column}
          onChange={(e) =>
            updateNode({
              config: { conditions: [{ ...first, column: e.target.value }] },
            })
          }
        />
        <label className="block text-xs text-zinc-400">Value</label>
        <Input
          value={String(first.value ?? "")}
          onChange={(e) =>
            updateNode({
              config: { conditions: [{ ...first, value: e.target.value }] },
            })
          }
        />
      </div>
    );
  }

  if (node.type === "output") {
    const config = node.config ?? {};
    return (
      <div className="space-y-3 border border-zinc-700 bg-zinc-900 p-4">
        <h3 className="text-sm font-medium">Output dataset</h3>
        <p className="text-xs text-zinc-500">
          Running the pipeline writes a new Iceberg table and registers it as a dataset.
        </p>
        <label className="block text-xs text-zinc-400">Table name</label>
        <Input
          value={String(config.table_name ?? "")}
          onChange={(e) =>
            updateNode({ config: { ...config, table_name: e.target.value, mode: "overwrite" } })
          }
        />
      </div>
    );
  }

  return <p className="text-sm text-zinc-500">No config for this node type.</p>;
}
