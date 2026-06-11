export interface LineageNodeData {
  id: string;
  label: string;
  node_type: "dataset" | "source" | "pipeline";
  entity_id: string;
  row_count?: number | null;
  connector_type?: string | null;
  last_run_status?: string | null;
  last_updated?: string | null;
}

export interface LineageGraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: LineageNodeData;
}

export interface LineageGraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string | null;
}

export interface LineageGraph {
  nodes: LineageGraphNode[];
  edges: LineageGraphEdge[];
}

export interface SnapshotHistoryItem {
  snapshot_id: number;
  committed_at: string | null;
  operation: string | null;
  summary: string | null;
}
