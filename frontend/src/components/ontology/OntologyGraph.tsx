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
import dagre from "dagre";
import { useEffect, useMemo } from "react";
import type { OntologyGraph as OntologyGraphType } from "@/types/ontology";
import { FlowCanvas } from "@/components/flow/FlowCanvas";

function layoutGraph(graph: OntologyGraphType) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", nodesep: 80, ranksep: 120 });

  graph.nodes.forEach((n) => g.setNode(n.id, { width: 180, height: 60 }));
  graph.edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return {
    nodes: graph.nodes.map((n) => {
      const pos = g.node(n.id);
      return {
        id: n.id,
        position: { x: pos.x - 90, y: pos.y - 30 },
        data: { label: String(n.data.label ?? n.data.name ?? n.id) },
        style: {
          background: String(n.data.color ?? "#312e81"),
          color: "#e0e7ff",
          border: "1px solid #6366f1",
          borderRadius: 0,
          padding: 8,
          minWidth: 160,
        },
      };
    }),
    edges: graph.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label ?? undefined,
    })),
  };
}

export function OntologyGraph({ graph }: { graph: OntologyGraphType }) {
  const laid = useMemo(() => layoutGraph(graph), [graph]);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    setNodes(laid.nodes);
    setEdges(laid.edges);
  }, [laid, setNodes, setEdges]);

  return (
    <div className="h-[500px] border border-zinc-700 bg-zinc-950">
      <FlowCanvas nodeCount={nodes.length}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
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
