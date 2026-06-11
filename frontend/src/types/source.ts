export type SourceType =
  | "csv"
  | "parquet"
  | "postgresql"
  | "mysql"
  | "s3"
  | "snowflake"
  | "bigquery"
  | "rest_api"
  | "kafka";

export interface Source {
  id: string;
  name: string;
  source_type: SourceType;
  is_active: boolean;
  schema_cache: { tables?: TableSchema[] } | null;
  schema_discovered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ColumnDef {
  name: string;
  type: string;
  nullable: boolean;
}

export interface TableSchema {
  name: string;
  columns: ColumnDef[];
}

export interface SchemaDiscovery {
  tables: TableSchema[];
  discovered_at: string | null;
}

export interface TestConnectionResult {
  connected: boolean;
}
