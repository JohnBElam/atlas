export interface Dataset {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  source_id: string | null;
  iceberg_namespace: string;
  iceberg_table: string;
  iceberg_location: string;
  schema_json: { fields?: { name: string; type: string }[] } | null;
  row_count: number | null;
  size_bytes: number | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
}

export interface ColumnProfile {
  name: string;
  type: string;
  distinct_count: number | null;
  null_count: number | null;
  non_null_count: number | null;
  min_value: unknown;
  max_value: unknown;
}

export interface DatasetProfile {
  row_count: number;
  columns: ColumnProfile[];
}

export interface IngestRequest {
  source_id: string;
  table_or_file: string;
  dataset_name: string;
  display_name: string;
  mode: "create" | "overwrite";
}
