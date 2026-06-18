export interface ObjectType {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  icon: string;
  color: string;
  primary_key_property_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ObjectProperty {
  id: string;
  object_type_id: string;
  name: string;
  display_name: string;
  data_type: string;
  is_required: boolean;
  dataset_id: string | null;
  column_name: string | null;
  description: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ObjectTypeDetail {
  type: ObjectType;
  properties: ObjectProperty[];
}

export type LinkCardinality = "one-to-one" | "one-to-many" | "many-to-many";

export interface LinkType {
  id: string;
  name: string;
  display_name: string;
  from_object_type_id: string;
  to_object_type_id: string;
  cardinality: LinkCardinality;
  from_property_id: string;
  to_property_id: string;
  description: string | null;
}

export interface OntologyGraph {
  nodes: { id: string; type: string; position: { x: number; y: number }; data: Record<string, unknown> }[];
  edges: { id: string; source: string; target: string; label?: string | null }[];
}

export interface ObjectList {
  columns: string[];
  rows: Record<string, unknown>[];
}
