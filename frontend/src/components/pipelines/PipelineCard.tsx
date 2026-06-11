import { Link } from "@tanstack/react-router";
import type { Pipeline } from "@/types/pipeline";

export function PipelineCard({ pipeline }: { pipeline: Pipeline }) {
  const nodeCount = pipeline.dag_json.nodes?.length ?? 0;
  return (
    <Link
      to="/pipelines/$id"
      params={{ id: pipeline.id }}
      className="block border border-zinc-700 bg-zinc-900 p-4 hover:border-indigo-600"
    >
      <h3 className="font-medium text-zinc-100">{pipeline.name}</h3>
      {pipeline.description && (
        <p className="mt-1 text-sm text-zinc-500">{pipeline.description}</p>
      )}
      <p className="mt-2 text-xs text-zinc-400">{nodeCount} nodes</p>
    </Link>
  );
}
