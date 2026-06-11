import { Handle, Position, type NodeProps } from "@xyflow/react";

export function OutputNode({ data }: NodeProps) {
  const config = (data as { config?: { table_name?: string } }).config;
  return (
    <div className="min-w-[140px] border border-emerald-500 bg-emerald-900 px-3 py-2 text-emerald-100">
      <div className="text-xs uppercase text-emerald-300">Output</div>
      <div className="font-data text-sm">{config?.table_name ?? "output"}</div>
      <Handle type="target" position={Position.Left} />
    </div>
  );
}
