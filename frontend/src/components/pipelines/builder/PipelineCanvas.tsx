import {
  Background,
  Controls,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useRef } from "react";
import type { PipelineDag, PipelineNode } from "@/types/pipeline";
import { FlowCanvas } from "@/components/flow/FlowCanvas";
import { OutputNode } from "./OutputNode";
import { SourceNode } from "./SourceNode";
import { TransformNode } from "./TransformNode";

const nodeTypes = {
  source: SourceNode,
  transform: TransformNode,
  output: OutputNode,
};

function nodeDataFromDag(n: PipelineNode, label?: string) {
  return {
    label:
      label ??
      (n.type === "transform" ? n.transform_type ?? "transform" : n.type),
    dataset_id: n.dataset_id,
    transform_type: n.transform_type,
    config: n.config ?? {},
  };
}

function dagToFlow(dag: PipelineDag): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = dag.nodes.map((n, i) => ({
    id: n.id,
    type: n.type,
    position: { x: 100 + (i % 3) * 220, y: 80 + Math.floor(i / 3) * 140 },
    data: nodeDataFromDag(n),
  }));
  const edges: Edge[] = dag.edges.map((e) => ({
    id: `${e.from}-${e.to}`,
    source: e.from,
    target: e.to,
  }));
  return { nodes, edges };
}

function flowToDag(nodes: Node[], edges: Edge[]): PipelineDag {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type as "source" | "transform" | "output",
      ...(n.type === "source"
        ? { dataset_id: (n.data as { dataset_id?: string }).dataset_id }
        : {}),
      ...(n.type === "transform"
        ? {
            transform_type:
              (n.data as { transform_type?: string }).transform_type ?? "filter",
            config:
              (n.data as { config?: Record<string, unknown> }).config ?? {},
          }
        : {}),
      ...(n.type === "output"
        ? {
            config: (n.data as { config?: Record<string, unknown> }).config ?? {
              table_name: "output_table",
              mode: "overwrite",
            },
          }
        : {}),
    })),
    edges: edges.map((e) => ({ from: e.source, to: e.target })),
  };
}

export function PipelineCanvas({
  dag,
  pipelineId,
  onChange,
  onNodeSelect,
}: {
  dag: PipelineDag;
  pipelineId: string;
  onChange: (dag: PipelineDag) => void;
  onNodeSelect: (nodeId: string | null) => void;
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const loadedPipelineId = useRef<string | null>(null);

  useEffect(() => {
    if (loadedPipelineId.current === pipelineId) return;
    loadedPipelineId.current = pipelineId;
    const { nodes: n, edges: e } = dagToFlow(dag);
    setNodes(n);
    setEdges(e);
  }, [pipelineId, dag, setNodes, setEdges]);

  useEffect(() => {
    if (loadedPipelineId.current !== pipelineId) return;

    const existingIds = new Set(nodes.map((n) => n.id));
    const added = dag.nodes.filter((n) => !existingIds.has(n.id));
    if (added.length === 0) return;

    setNodes((prev) => [
      ...prev,
      ...added.map((n, i) => {
        const idx = prev.length + i;
        return {
          id: n.id,
          type: n.type,
          position: {
            x: 100 + (idx % 3) * 220,
            y: 80 + Math.floor(idx / 3) * 140,
          },
          data: nodeDataFromDag(n),
        };
      }),
    ]);
  }, [dag.nodes, nodes, pipelineId, setNodes]);

  useEffect(() => {
    if (loadedPipelineId.current !== pipelineId) return;

    setNodes((prev) =>
      prev.map((flowNode) => {
        const dagNode = dag.nodes.find((n) => n.id === flowNode.id);
        if (!dagNode) return flowNode;
        return {
          ...flowNode,
          data: nodeDataFromDag(dagNode),
        };
      }),
    );
  }, [dag, pipelineId, setNodes]);

  const emitChange = useCallback(
    (nextNodes: Node[], nextEdges: Edge[]) => {
      onChange(flowToDag(nextNodes, nextEdges));
    },
    [onChange],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const nextEdges = addEdge(connection, eds);
        setNodes((nds) => {
          emitChange(nds, nextEdges);
          return nds;
        });
        return nextEdges;
      });
    },
    [setEdges, setNodes, emitChange],
  );

  const handleNodesChange = useCallback(
    (...args: Parameters<typeof onNodesChange>) => {
      onNodesChange(...args);
      setNodes((currentNodes) => {
        setEdges((currentEdges) => {
          emitChange(currentNodes, currentEdges);
          return currentEdges;
        });
        return currentNodes;
      });
    },
    [onNodesChange, emitChange, setNodes, setEdges],
  );

  const handleEdgesChange = useCallback(
    (...args: Parameters<typeof onEdgesChange>) => {
      onEdgesChange(...args);
      setNodes((currentNodes) => {
        setEdges((currentEdges) => {
          emitChange(currentNodes, currentEdges);
          return currentEdges;
        });
        return currentNodes;
      });
    },
    [onEdgesChange, emitChange, setNodes, setEdges],
  );

  return (
    <div className="h-[500px] border border-zinc-700 bg-zinc-950">
      <FlowCanvas nodeCount={nodes.length}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          onSelectionChange={({ nodes: selected }) =>
            onNodeSelect(selected[0]?.id ?? null)
          }
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
