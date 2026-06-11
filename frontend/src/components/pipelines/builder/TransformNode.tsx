import { Handle, Position, type NodeProps } from "@xyflow/react";

export function TransformNode({ data }: NodeProps) {
  const label = (data as { label?: string }).label ?? "transform";
  return (
    <div className="min-w-[140px] border border-orange-500 bg-orange-900 px-3 py-2 text-orange-100">
      <div className="text-xs uppercase text-orange-300">Transform</div>
      <div className="font-data text-sm">{label}</div>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
