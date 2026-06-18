import {
  Background,
  Controls,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo } from "react";
import type { LineageGraph as LineageGraphType } from "@/types/lineage";
import { FlowCanvas } from "@/components/flow/FlowCanvas";
import {
  resolveLineageLayout,
  updateLineagePosition,
} from "@/lib/lineage-layout";
import { LineageNode } from "./LineageNode";

const nodeTypes = { lineage: LineageNode };

export function LineageGraph({
  graph,
  onNodeClick,
}: {
  graph: LineageGraphType;
  onNodeClick: (nodeId: string) => void;
}) {
  const layout = useMemo(() => resolveLineageLayout(graph), [graph]);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    setNodes(
      graph.nodes.map((n) => ({
        id: n.id,
        type: "lineage",
        position: layout.positions[n.id] ?? { x: 0, y: 0 },
        data: n.data as unknown as Record<string, unknown>,
      })),
    );
    setEdges(
      graph.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label ?? undefined,
      })),
    );
  }, [graph, layout, setNodes, setEdges]);

  const onNodeDragStop = useCallback(
    (_: MouseEvent | TouchEvent, node: Node) => {
      updateLineagePosition(node.id, node.position);
    },
    [],
  );

  return (
    <div className="h-[600px] border border-zinc-700 bg-zinc-950">
      <FlowCanvas nodeCount={nodes.length} fitView={layout.shouldFitView}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => onNodeClick(node.id)}
          nodesConnectable={false}
          colorMode="dark"
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#3f3f46" gap={16} />
          <Controls />
        </ReactFlow>
      </FlowCanvas>
    </div>
  );
}
