import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { LineageNodeData } from "@/types/lineage";

const styles: Record<string, string> = {
  dataset: "border-blue-500 bg-blue-900 text-blue-100",
  source: "border-green-500 bg-green-900 text-green-100",
  pipeline: "border-orange-500 bg-orange-900 text-orange-100",
};

export function LineageNode({ data }: NodeProps) {
  const nodeData = data as unknown as LineageNodeData;
  const style = styles[nodeData.node_type] ?? "border-zinc-500 bg-zinc-800";
  return (
    <div className={`min-w-[160px] border px-3 py-2 ${style}`}>
      <div className="text-xs uppercase opacity-70">{nodeData.node_type}</div>
      <div className="text-sm font-medium">{nodeData.label}</div>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
