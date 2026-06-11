export interface PipelineNode {
  id: string;
  type: "source" | "transform" | "output";
  dataset_id?: string;
  transform_type?: string;
  config?: Record<string, unknown>;
}

export interface PipelineEdge {
  from: string;
  to: string;
}

export interface PipelineDag {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

export interface Pipeline {
  id: string;
  name: string;
  description: string | null;
  dag_json: PipelineDag;
  schedule_cron: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  status: "queued" | "running" | "success" | "failed" | "cancelled";
  triggered_by: string;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  rows_read: number | null;
  rows_written: number | null;
  target_dataset_id: string | null;
  iceberg_snapshot_id: number | null;
  error_message: string | null;
  created_at: string;
}

export interface RunLogs {
  lines: string[];
  next_since: number;
}
