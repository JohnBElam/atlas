import { Handle, Position, type NodeProps } from "@xyflow/react";

export function SourceNode({ data }: NodeProps) {
  const label = (data as { label?: string }).label ?? "source";
  return (
    <div className="min-w-[140px] border border-blue-500 bg-blue-900 px-3 py-2 text-blue-100">
      <div className="text-xs uppercase text-blue-300">Source</div>
      <div className="font-data text-sm">{label}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
