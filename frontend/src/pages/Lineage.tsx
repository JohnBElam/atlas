import { useLineageGraph } from "@/api/lineage";
import { AppShell } from "@/components/layout/AppShell";
import { LineageDetailPanel } from "@/components/lineage/LineageDetailPanel";
import { LineageGraph } from "@/components/lineage/LineageGraph";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Skeleton } from "@/components/ui/Skeleton";
import { useLineageStore } from "@/stores/lineage-store";
import { getErrorMessage } from "@/lib/errors";
import type { LineageNodeData } from "@/types/lineage";

export function LineagePage() {
  const { data: graph, isLoading, isError, error } = useLineageGraph();
  const selectedNodeId = useLineageStore((s) => s.selectedNodeId);
  const setSelectedNodeId = useLineageStore((s) => s.setSelectedNodeId);

  const selectedNode: LineageNodeData | null =
    graph?.nodes.find((n) => n.id === selectedNodeId)?.data ?? null;

  return (
    <AppShell title="Lineage">
      {isLoading ? (
        <Skeleton className="h-[600px]" />
      ) : isError ? (
        <ErrorMessage message={getErrorMessage(error)} />
      ) : graph && graph.nodes.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
          <LineageGraph
            graph={graph}
            onNodeClick={(nodeId) => setSelectedNodeId(nodeId)}
          />
          <LineageDetailPanel node={selectedNode} />
        </div>
      ) : (
        <p className="text-sm text-zinc-500">
          No lineage data yet. Ingest a dataset or run a pipeline to populate the graph.
        </p>
      )}
    </AppShell>
  );
}
