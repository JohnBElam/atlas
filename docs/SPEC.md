# ATLAS Platform — Build Specification

ATLAS is a local-first data operations workbench inspired by Palantir Foundry concepts. It is a commercial product in development: it will eventually be licensed to customers and dogfooded in the builder's own client deployments. Phase 1 is intentionally small, but the data model must protect that commercial future.

The product has four pillars: **data ingestion**, **data lineage**, **data ontology**, and **no-code analytics**. There is no AI layer. Build exactly what is specified. Do not add features not listed here. Do not deviate from the tech stack.

Execution order and slice gates live in [`BUILD_PLAN.md`](BUILD_PLAN.md). Architecture decisions live in [`DECISIONS.md`](DECISIONS.md).

---

## Spec Corrections

This document resolves defects found in prior spec versions. Do not reintroduce them.

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Project named NEXUS | Renamed **ATLAS** everywhere: project name, database, buckets, env vars, repo folder. |
| 2 | Lineage model incorrect | Iceberg snapshots are table-state evidence, not lineage. System of record is `lineage_events` + `lineage_event_inputs`. Removed `source_dataset_ids UUID[]` in favor of normalized inputs. `iceberg_snapshot_id` is nullable because a write can legitimately produce no new snapshot. |
| 3 | Scale claim overstated | Phase 1 does **not** handle billions of rows. Abstractions (`ComputeEngine`, Iceberg, catalog) must not block later migration to distributed compute. See [Future Scale Constraints](#future-scale-constraints). |
| 4 | Soft-delete vs CASCADE | Removed `ON DELETE CASCADE` from `object_properties` and `widgets`. Added `deleted_at` to `widgets`. Soft deletes enforced in service layer. No hard deletes on mutable entities. |
| 5 | Tenancy | `organization_id` and `created_by` (UUID NULL) on all major mutable tables. Phase 1 logic ignores them entirely. |
| 6 | Audit | New `audit_events` table; service-layer writes on create, update, soft-delete, pipeline run. No audit UI in Phase 1. |
| 7 | Connector list inconsistent | Phase 1 implements **CSV, Parquet, PostgreSQL** only. MySQL, S3, Snowflake, BigQuery, REST API, Kafka are stubs. |
| 8 | Pipeline node scope | Phase 1: source, filter, select, rename, cast, derive, sort, limit, deduplicate, output. Joins and aggregates are Phase 2 (config formats documented for forward compatibility). |
| 9 | Pipeline validation | Reject cycles, multiple outputs, unreachable nodes, unknown transform types. Identifier sanitization and value parameterization required. |
| 10 | Ontology resolution | Primary key required for object browsing. Multi-dataset types only when every backing dataset maps the PK column. No join inference. Incomplete mappings → 400. |
| 11 | Public dashboard sharing | Removed from Phase 1. Schema columns `is_public`, `public_token` remain; routes and publish endpoint deferred. |
| 12 | Dataset ingestion | Added `POST /api/v1/datasets/ingest` contract. |
| 13 | CSV upload guardrails | Filename sanitization, configurable size limit (default 500 MB), empty-file rejection. |
| 14 | Log delivery order | HTTP polling first; WebSocket only after polling works end-to-end. |
| 15 | Missing indexes | Added indexes for soft-delete filters and common lookups. |
| 16 | `deleted_at` on all tables vs append-only tables | **Append-only event tables** (`pipeline_runs`, `lineage_event_inputs`, `audit_events`) are exempt from soft-delete. Immutable history; no DELETE routes in Phase 1. `lineage_events` retains `deleted_at` for administrative correction without breaking FK integrity on inputs. |
| 17 | Bind to localhost vs no localhost in code | **Not a contradiction.** Docker Compose and `.env.example` bind localhost for local dev. Application code reads all hosts, URLs, and paths from pydantic-settings only. |
| 18 | Phase 1 scale vs end-state product vision | Phase 1 targets single-user, single-node DuckDB workloads (thousands–millions of rows in practice). End-state (billions of rows queryable, thousands of users, hundreds of connectors) is a **design constraint**, not a Phase 1 deliverable. |
| 19 | Widget build order vs layout order | Build order: Dashboard CRUD → `table` → `metric_card` → `bar_chart` → dropdown `filter` → **layout save/load** → `text`. Text widget is last; layout persistence ships after filter widget works. |
| 20 | Metric widget naming | Canonical DB/API enum is `metric_card` (matches CHECK constraint). |

---

## Product Overview

### What it is

A web application that lets data teams ingest raw data from multiple sources, track the lineage of how data flows and transforms, define a semantic ontology of business objects, and build dashboards without writing code.

### What it is not

- An AI assistant
- A BI tool that connects to external dashboards
- A data warehouse
- A Palantir clone

It is a metadata and pipeline orchestration platform that sits on top of object storage.

### Commercial context

ATLAS will be licensed as self-hosted software and used in the builder's own client deployments. Phase 1 is single-user and local-only, but:

- The schema carries tenancy and ownership columns from the first migration.
- Audit history accumulates from day one.
- No application code may assume localhost. All endpoints, paths, and secrets come from configuration.

### Four pillars (Phase 1)

1. **Data ingestion** — register CSV, Parquet, and PostgreSQL sources; ingest into Apache Iceberg on MinIO
2. **Data lineage** — automatic lineage from pipeline execution events; Iceberg snapshots as supporting evidence
3. **Data ontology** — business object types mapped column-level to dataset columns
4. **No-code analytics** — drag-and-drop dashboards with table, metric card, bar chart, and dropdown filter widgets

### Non-negotiables

- Phase 1 abstractions must not block later migration to distributed compute (Spark, Trino, ClickHouse). Phase 1 itself targets single-node DuckDB workloads.
- Lineage tracking must be automatic. The user never annotates anything.
- The ontology layer must allow column-level mapping from datasets to business object properties.
- Dashboards must be buildable entirely through drag-and-drop.

### Phase 1 deployment posture

Local development only. Bind to localhost via Compose. No public routes. No auth. Acceptable only because deployment is local and single-user.

### Future Scale Constraints

The long-term product must support:

- **Billions of rows** queryable and visualizable (via distributed compute and production serving layers not built in Phase 1)
- **Thousands of users** (via auth, RBAC, and tenancy features not built in Phase 1)
- **Hundreds of data source types** (via the `Connector` protocol and stub registry; Phase 1 implements three)

Phase 1 designs interfaces (`ComputeEngine`, `Connector`, normalized lineage, tenancy columns, paginated APIs, Iceberg table format) so these capabilities are **feature additions**, not rewrites. Do not claim Phase 1 performance at end-state scale.

### Phase 1 non-goals

- Authentication, RBAC, user management
- Scheduling (cron triggers)
- Public dashboard sharing
- Spark execution (stub only)
- Join and aggregate pipeline nodes
- Link traversal UI (API only for link traversal)
- Production connectors beyond CSV, Parquet, PostgreSQL (MySQL, S3, Snowflake, BigQuery, REST, Kafka are stubs)
- Production hardening and high-concurrency dashboard serving
- AI features
- Audit UI
- `ontology_query` widget binding

---

## Tech Stack

### Backend

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | |
| API framework | FastAPI 0.110+ | Async, OpenAPI auto-docs |
| ORM | SQLAlchemy 2.0 async | |
| Migrations | Alembic | |
| Validation | Pydantic v2 | |
| Task queue | Celery 5 + Redis 7 | Async pipeline execution |
| Metadata DB | PostgreSQL 15+ | All platform metadata |
| Table format | Apache Iceberg via PyIceberg 0.7+ | ACID, snapshots, time travel |
| Object storage | MinIO (local) / S3-compatible (later) | Iceberg data files |
| Default compute | DuckDB 0.10+ | Single-node OLAP, native Iceberg, native Parquet |
| Fallback compute | Apache Spark (stub only) | Wire interface; do not implement |
| Credential encryption | cryptography (Fernet) | Stored source configs |

### Frontend

| Component | Choice |
|---|---|
| Framework | React 18 + TypeScript 5 |
| Build | Vite 5 |
| Styling | Tailwind CSS 3 + shadcn/ui |
| Routing | TanStack Router v1 |
| Data fetching | TanStack Query v5 |
| Tables | TanStack Table v8 |
| Graph / DAG canvas | React Flow 11 |
| Drag-and-drop | dnd-kit |
| Charts | Recharts 2 |
| State | Zustand 4 |
| Icons | lucide-react |

### Infrastructure (Docker Compose for local dev)

- `postgres:15` — metadata database
- `redis:7-alpine` — Celery broker + result backend
- `minio/minio` — S3-compatible object storage; buckets: `atlas-data`, `atlas-iceberg`
- `mher/flower` — Celery task monitor at :5555

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ATLAS Frontend                          │
│  Sources │ Datasets │ Pipelines │ Lineage │ Ontology │ Workshop │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST (+ WebSocket after polling works)
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                               │
│   /api/v1/{sources, datasets, pipelines, lineage,               │
│             ontology, analytics, ws}                             │
│                                                                  │
│  Services → ComputeEngine (Protocol)                             │
│                ├── DuckDBEngine  (default)                       │
│                └── SparkEngine   (stub, not implemented Ph.1)    │
└──────┬───────────────────────────┬──────────────────────────────┘
       │                           │
┌──────▼──────┐          ┌─────────▼─────────────────────────────┐
│  PostgreSQL │          │  Apache Iceberg (via PyIceberg)         │
│  (metadata) │          │  ├── Datasets (Parquet files)           │
│             │          │  ├── Snapshots (state evidence)         │
│  sources    │          │  └── SQL catalog (Postgres)             │
│  datasets   │          └─────────────┬─────────────────────────┘
│  pipelines  │                        │ s3a://
│  lineage    │          ┌─────────────▼──────┐
│  ontology   │          │  MinIO / S3        │
│  analytics  │          │  atlas-iceberg/    │
│  audit      │          │  atlas-data/       │
└─────────────┘          └────────────────────┘
Celery Workers ← Redis ← FastAPI (pipeline trigger)
     │
     └── PipelineExecutor → DuckDBEngine → PyIceberg write
```

### Lineage events are the system of record

Iceberg snapshots provide immutable table-state evidence: what changed, when, how many records, which files. They do not know pipeline intent, source-to-target semantics, or cross-table dependency meaning.

ATLAS lineage is built from **pipeline execution events**:

- `lineage_events` records every ingest and transform.
- `lineage_event_inputs` records every input (source or dataset) per event, one row each.
- Iceberg snapshot IDs attach to lineage events **when available**. A write that produces no new snapshot still records a lineage event with `iceberg_snapshot_id = NULL`.
- The lineage graph is constructed exclusively from these tables. Snapshot history is supplementary detail on dataset pages.

Sidebar navigation and frontend routes are delivered incrementally per [`BUILD_PLAN.md`](BUILD_PLAN.md); do not ship all modules on day one.

---

## Module Specifications

### Data Source Registry

**Purpose:** Register, test, and discover schema from external data sources.

**Implemented connector types (Phase 1):**

- `csv` — file upload, stored to MinIO `atlas-data/uploads/{source_id}/{safe_filename}`
- `parquet` — file upload, same path scheme (PyArrow reads alongside CSV)
- `postgresql` — connection string

**Stub connectors (wire class, raise `NotImplementedError`):**

- `mysql`, `s3`, `snowflake`, `bigquery`, `rest_api`, `kafka`

**Connector Protocol:**

```python
class Connector(Protocol):
    def test_connection(self) -> bool: ...
    def list_tables(self) -> list[str]: ...  # or files for file-based
    def get_schema(self, table: str) -> list[ColumnDef]: ...
    def read_table(self, table: str, limit: int | None) -> pa.Table: ...
```

**Credential handling:** Source config stored encrypted (Fernet) in `config_encrypted`. Decryption only inside the service layer. Never log decrypted credentials. Never return them through the API, including in error messages.

**File upload guardrails:**

- Sanitize filenames (strip path separators, control characters; enforce safe charset).
- Reject empty files.
- Enforce configurable max file size (default 500 MB from settings).

**PostgreSQL connector:** test connection, list tables, get schema, read table with optional limit. No arbitrary user SQL against the source in Phase 1.

**Schema discovery:** On "Discover Schema", call `list_tables()` and `get_schema()` for each; cache in `schema_cache` (JSONB on `data_sources`) with `schema_discovered_at`. `?refresh=true` forces re-discovery.

For file-based CSV/Parquet sources, `list_tables()` returns uploaded filenames from the MinIO prefix for that source (see DECISIONS.md A3).

---

### Ingestion Pipeline Engine

**Purpose:** Define transform pipelines as DAGs, execute against ingested data, write results as Iceberg tables.

**Pipeline DAG format** (stored as `dag_json` JSONB in `pipeline_definitions`):

```json
{
  "nodes": [
    { "id": "n1", "type": "source", "dataset_id": "<uuid>" },
    { "id": "n2", "type": "transform", "transform_type": "filter",
      "config": { "conditions": [{ "column": "status", "operator": "eq", "value": "active" }] }},
    { "id": "n3", "type": "output",
      "config": { "namespace": "default", "table_name": "active_orders", "mode": "overwrite" }}
  ],
  "edges": [
    { "from": "n1", "to": "n2" },
    { "from": "n2", "to": "n3" }
  ]
}
```

**Transform types — Phase 1:**

| Type | Config fields |
|---|---|
| `filter` | `conditions: [{column, operator, value}]` — operators: eq, neq, gt, gte, lt, lte, in, not_in, is_null, is_not_null |
| `select` | `columns: string[]` |
| `rename` | `mapping: {old_name: new_name}` |
| `cast` | `columns: [{column, to_type}]` — types: string, integer, float, boolean, date, timestamp |
| `derive` | `expressions: [{name, expr}]` — DuckDB SQL expressions allowed |
| `sort` | `columns: [{column, direction}]` |
| `limit` | `n: integer` |
| `deduplicate` | `subset: string[] \| null` |

**Transform types — Phase 2 (document only):**

| Type | Config fields |
|---|---|
| `aggregate` | `group_by: string[], aggregations: [{column, func, alias}]` |
| `join` | `right_node_id, left_on, right_on, how` |

**On `derive`:** Arbitrary DuckDB SQL expressions permitted in Phase 1 (single-user local tool). Expression validated as scalar (no statements, no semicolons). **Gate `derive` behind RBAC when multi-user lands.** Identifier sanitization, column quoting, and value parameterization in the CTE builder are mandatory for correctness.

**DAG validation (400 before queuing):**

- Acyclic DAG
- Exactly one output node
- Every transform reachable from a source; output reachable from every node
- Unknown transform types rejected
- Unknown node references in edges rejected

**SQL construction safety:**

- Node IDs sanitized before becoming SQL identifiers (alphanumeric + underscore, prefixed)
- All column names quoted
- All filter values parameterized
- `derive` expressions wrapped, never concatenated into other clauses

**Pipeline Executor** (`app/pipeline/executor.py`):

1. Validate DAG
2. Topological sort
3. Build single SQL query using CTEs
4. Source nodes: `cte_name AS (SELECT * FROM iceberg_scan('<s3_path>'))`
5. Execute via DuckDB, get Arrow result
6. Write to Iceberg via PyIceberg `.overwrite()` or `.append()`
7. Capture snapshot ID if produced; else null
8. Create or update output `datasets` record
9. Write `lineage_events` + `lineage_event_inputs`
10. Write `audit_events` row for the run
11. Update `pipeline_runs` with status, rows_written, snapshot_id

**Execution:** Always async via Celery. Trigger returns `{ run_id, status: "queued" }` immediately.

**Log delivery order:**

1. Celery appends log lines to Redis list `pipeline:logs:{run_id}`
2. `GET /pipelines/runs/{run_id}/logs?since=0` — ship first
3. WebSocket at `/ws/pipeline-runs/{run_id}` — only after polling works

---

### Data Lineage

**Graph node types:**

- **Dataset** (blue): Iceberg table registered in ATLAS
- **Source** (green): external data source
- **Pipeline** (orange): pipeline definition

**Edges:** Source → Pipeline, Dataset → Pipeline, Pipeline → Dataset (labeled with pipeline name + last run timestamp).

**Data source:** Graph built **exclusively** from `lineage_events` and `lineage_event_inputs`. Iceberg snapshot history is supplementary in the dataset panel, not merged into the graph.

**API:**

- `GET /lineage/dataset/{id}` — subgraph, N hops (default 3)
- `GET /lineage/graph` — full graph in React Flow format
- `GET /lineage/dataset/{id}/snapshots` — Iceberg snapshot history

**Frontend styling (not default React Flow):**

- Dataset: `bg-blue-900 border border-blue-500 text-blue-100`, sharp corners
- Source: `bg-green-900 border border-green-500 text-green-100`
- Pipeline: `bg-orange-900 border border-orange-500 text-orange-100`

Detail panel: name, type, last updated, row count (datasets), connector type (sources), last run status (pipelines). Pipeline nodes: "View Pipeline" link, last 5 run statuses. Dataset nodes: last 5 pipeline runs, snapshot history.

---

### Data Ontology

**Concepts:**

- **Object Type** — named business entity (e.g., Supplier, Part)
- **Object Property** — attribute backed by a dataset column
- **Link Type** — directed relationship between two Object Types
- **Object Instance** — row resolved by querying backing datasets

**Object Type:** `name` (slug, unique), `display_name`, `description`, `icon` (lucide), `color` (hex), `primary_key_property_id` (FK, set after properties exist).

**Object Property:** `name`, `display_name`, `data_type`, `dataset_id` + `column_name`, `is_required`, `sort_order`.

**Link Type:** `name`, `display_name`, `from_object_type_id`, `to_object_type_id`, `from_property_id`, `to_property_id`, `cardinality` (one-to-one | one-to-many | many-to-many).

**Resolution rules:**

- Object browsing requires primary key property → 400 if unset
- Single-dataset object types fully supported
- Multi-dataset only when every backing dataset maps the primary key column; join on that key
- Never infer joins
- Incomplete mappings → 400

**Resolution procedure** (`GET /ontology/types/{id}/objects`):

1. Load Object Type and Properties
2. Validate rules; 400 on violation
3. Group properties by `dataset_id`
4. Build DuckDB SQL from Iceberg tables; join on PK if multi-dataset
5. Return paginated results

**Link traversal:** `GET /ontology/types/{id}/objects/{pk}/links/{link_type_id}` — API only in Phase 1.

**Frontend:** Ontology graph (React Flow + dagre), Object Type Editor, Property Mapper (dataset/column dropdowns).

Primary key set via `PUT /ontology/types/{id}` after properties exist (deferred FK; see DECISIONS.md A5).

---

### Workshop (No-Code Analytics)

**Layout:** JSON in `dashboards.layout_json`:

```json
[
  { "widget_id": "<uuid>", "x": 0, "y": 0, "w": 6, "h": 4 }
]
```

Grid: 12 columns, unlimited rows, 80px cells, snap to grid. dnd-kit repositioning, resize handle bottom-right.

**Widget build order (Phase 1):**

| Order | Type | Config fields |
|---|---|---|
| 1 | `table` | `columns: string[] \| null`, `page_size`, `sortable`, `filterable` |
| 2 | `metric_card` | `value_column`, `aggregation`, `label`, `format`, `prefix`, `suffix` |
| 3 | `bar_chart` | `x_axis`, `y_axis`, `color_by`, `aggregation` |
| 4 | `filter` | `filter_type: "dropdown"`, `source_column`, `label`, `applies_to`, `multi_select` |
| 5 | Layout save/load | dnd-kit grid, `layout_json` persistence, viewer route |
| 6 | `text` | `content` (Markdown) |

Do not start a later widget until the previous one works end-to-end.

**Widget Types — Phase 2 (CHECK constraint includes them now):** `line_chart`, `pie_chart`, date range and search filter types.

**Data binding:**

```typescript
interface DataBinding {
  source_type: 'dataset' | 'ontology_query';
  dataset_id?: string;
  object_type_id?: string;
  properties?: string[];
  filters?: FilterCondition[];
  limit?: number;
}
```

Phase 1 implements `source_type: 'dataset'` only.

**Widget data query** (`POST /analytics/widgets/{id}/data`):

- Request body: current filter state from active filter widgets
- Merge with widget binding filters
- Execute via DuckDB; parameterized filters
- Return `{ columns, rows, total }`

**Filter state:** Zustand store. Filter widgets broadcast; data widgets subscribe and re-query. `applies_to` references widget IDs (see DECISIONS.md A4).

**UI:** Left palette (240px), center canvas, right config panel (320px). Top bar: name, Save, Preview. Viewer at `/workshop/{id}/view` (read-only, filters work).

**Public sharing:** Phase 2. No publish endpoint, no Share button, no `/public/{token}` route.

---

## Database Schema (PostgreSQL)

Run via Alembic. UUID primary keys via `gen_random_uuid()`. `TIMESTAMPTZ` for all timestamps.

**Universal rules (mutable entities):**

- `organization_id UUID NULL` and `created_by UUID NULL` on major tables; Phase 1 ignores them
- `deleted_at TIMESTAMPTZ NULL`; soft deletes in service layer
- **No `ON DELETE CASCADE` anywhere**
- No hard deletes on mutable entities
- All service queries filter `deleted_at IS NULL` by default
- Reject references to soft-deleted parents

**Append-only tables (correction #16):** `pipeline_runs`, `lineage_event_inputs`, and `audit_events` have no `deleted_at` and no DELETE API in Phase 1.

```sql
-- Data Sources
CREATE TABLE data_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  source_type TEXT NOT NULL
    CHECK (source_type IN ('csv','parquet','postgresql','mysql','s3','snowflake','bigquery','rest_api','kafka')),
  config_encrypted BYTEA NOT NULL,
  schema_cache JSONB,
  schema_discovered_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_data_sources_deleted_at ON data_sources(deleted_at);
CREATE INDEX idx_data_sources_source_type ON data_sources(source_type);
CREATE UNIQUE INDEX uq_data_sources_name_active ON data_sources(name) WHERE deleted_at IS NULL;

-- Datasets
CREATE TABLE datasets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  source_id UUID REFERENCES data_sources(id),
  iceberg_namespace TEXT NOT NULL DEFAULT 'default',
  iceberg_table TEXT NOT NULL,
  iceberg_location TEXT NOT NULL,
  schema_json JSONB,
  row_count BIGINT,
  size_bytes BIGINT,
  last_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,
  UNIQUE(iceberg_namespace, iceberg_table)
);
CREATE INDEX idx_datasets_deleted_at ON datasets(deleted_at);
CREATE INDEX idx_datasets_source_id ON datasets(source_id);

-- Pipeline Definitions
CREATE TABLE pipeline_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  description TEXT,
  dag_json JSONB NOT NULL,
  schedule_cron TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_pipeline_definitions_deleted_at ON pipeline_definitions(deleted_at);
CREATE UNIQUE INDEX uq_pipeline_definitions_name_active ON pipeline_definitions(name) WHERE deleted_at IS NULL;

-- Pipeline Runs (append-only)
CREATE TABLE pipeline_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  pipeline_id UUID NOT NULL REFERENCES pipeline_definitions(id),
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','running','success','failed','cancelled')),
  triggered_by TEXT NOT NULL DEFAULT 'manual'
    CHECK (triggered_by IN ('manual','schedule','api')),
  celery_task_id TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  rows_read BIGINT,
  rows_written BIGINT,
  target_dataset_id UUID REFERENCES datasets(id),
  iceberg_snapshot_id BIGINT,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pipeline_runs_pipeline_id ON pipeline_runs(pipeline_id);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_created_at ON pipeline_runs(created_at);

-- Lineage Events
CREATE TABLE lineage_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  event_type TEXT NOT NULL CHECK (event_type IN ('ingest','transform')),
  target_dataset_id UUID NOT NULL REFERENCES datasets(id),
  pipeline_run_id UUID REFERENCES pipeline_runs(id),
  iceberg_snapshot_id BIGINT,
  transform_summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_lineage_events_target ON lineage_events(target_dataset_id);
CREATE INDEX idx_lineage_events_run ON lineage_events(pipeline_run_id);
CREATE INDEX idx_lineage_events_deleted_at ON lineage_events(deleted_at);

-- Lineage Event Inputs (append-only)
CREATE TABLE lineage_event_inputs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lineage_event_id UUID NOT NULL REFERENCES lineage_events(id),
  input_type TEXT NOT NULL CHECK (input_type IN ('source','dataset')),
  source_id UUID REFERENCES data_sources(id),
  dataset_id UUID REFERENCES datasets(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    (input_type = 'source'  AND source_id IS NOT NULL AND dataset_id IS NULL) OR
    (input_type = 'dataset' AND dataset_id IS NOT NULL AND source_id IS NULL)
  )
);
CREATE INDEX idx_lineage_event_inputs_event ON lineage_event_inputs(lineage_event_id);
CREATE INDEX idx_lineage_event_inputs_dataset ON lineage_event_inputs(dataset_id);
CREATE INDEX idx_lineage_event_inputs_source ON lineage_event_inputs(source_id);

-- Audit Events (append-only)
CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  actor UUID,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID NOT NULL,
  payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);

-- Object Types
CREATE TABLE object_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  icon TEXT NOT NULL DEFAULT 'box',
  color TEXT NOT NULL DEFAULT '#6366f1',
  primary_key_property_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_object_types_deleted_at ON object_types(deleted_at);
CREATE UNIQUE INDEX uq_object_types_name_active ON object_types(name) WHERE deleted_at IS NULL;

-- Object Properties
CREATE TABLE object_properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  object_type_id UUID NOT NULL REFERENCES object_types(id),
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  data_type TEXT NOT NULL
    CHECK (data_type IN ('string','integer','float','boolean','date','datetime','json')),
  is_required BOOLEAN NOT NULL DEFAULT false,
  dataset_id UUID REFERENCES datasets(id),
  column_name TEXT,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_object_properties_type ON object_properties(object_type_id);
CREATE INDEX idx_object_properties_deleted_at ON object_properties(deleted_at);
CREATE UNIQUE INDEX uq_object_properties_name_active ON object_properties(object_type_id, name) WHERE deleted_at IS NULL;

ALTER TABLE object_types
  ADD CONSTRAINT fk_primary_key_property
  FOREIGN KEY (primary_key_property_id) REFERENCES object_properties(id)
  DEFERRABLE INITIALLY DEFERRED;

-- Link Types
CREATE TABLE link_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  from_object_type_id UUID NOT NULL REFERENCES object_types(id),
  to_object_type_id UUID NOT NULL REFERENCES object_types(id),
  cardinality TEXT NOT NULL
    CHECK (cardinality IN ('one-to-one','one-to-many','many-to-many')),
  from_property_id UUID NOT NULL REFERENCES object_properties(id),
  to_property_id UUID NOT NULL REFERENCES object_properties(id),
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_link_types_deleted_at ON link_types(deleted_at);
CREATE UNIQUE INDEX uq_link_types_name_active ON link_types(name) WHERE deleted_at IS NULL;

-- Dashboards
CREATE TABLE dashboards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  name TEXT NOT NULL,
  description TEXT,
  layout_json JSONB NOT NULL DEFAULT '[]',
  is_public BOOLEAN NOT NULL DEFAULT false,
  public_token TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_dashboards_deleted_at ON dashboards(deleted_at);

-- Widgets
CREATE TABLE widgets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID,
  created_by UUID,
  dashboard_id UUID NOT NULL REFERENCES dashboards(id),
  widget_type TEXT NOT NULL
    CHECK (widget_type IN ('table','bar_chart','line_chart','pie_chart','metric_card','text','filter')),
  title TEXT,
  config_json JSONB NOT NULL DEFAULT '{}',
  data_binding_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_widgets_dashboard_id ON widgets(dashboard_id);
CREATE INDEX idx_widgets_deleted_at ON widgets(deleted_at);
```

---

## API Contracts

All responses use:

```typescript
{ data: T | null, error: string | null, meta: Record<string, unknown> }
```

`meta` carries pagination: `{ page, page_size, total, total_pages }`.

HTTP status: 200, 201, 400, 404, 409, 500. **Never return 200 with an error message.**

### Routes

```
GET    /api/v1/health
GET    /api/v1/sources                      ?page&page_size&search
POST   /api/v1/sources
GET    /api/v1/sources/{id}
PUT    /api/v1/sources/{id}
DELETE /api/v1/sources/{id}
POST   /api/v1/sources/{id}/test
GET    /api/v1/sources/{id}/schema          ?refresh=false
POST   /api/v1/sources/{id}/upload
GET    /api/v1/datasets                     ?page&page_size&search&source_id
POST   /api/v1/datasets/ingest
GET    /api/v1/datasets/{id}
PUT    /api/v1/datasets/{id}
DELETE /api/v1/datasets/{id}
GET    /api/v1/datasets/{id}/preview        ?limit=100
GET    /api/v1/datasets/{id}/profile
GET    /api/v1/datasets/{id}/schema
GET    /api/v1/pipelines                    ?page&page_size&search
POST   /api/v1/pipelines
GET    /api/v1/pipelines/{id}
PUT    /api/v1/pipelines/{id}
DELETE /api/v1/pipelines/{id}
POST   /api/v1/pipelines/{id}/run
GET    /api/v1/pipelines/{id}/runs          ?page&page_size
GET    /api/v1/pipelines/runs/{run_id}
GET    /api/v1/pipelines/runs/{run_id}/logs ?since=0
GET    /api/v1/lineage/graph
GET    /api/v1/lineage/dataset/{id}         ?hops=3
GET    /api/v1/lineage/dataset/{id}/snapshots
GET    /api/v1/ontology/types               ?page&page_size
POST   /api/v1/ontology/types
GET    /api/v1/ontology/types/{id}
PUT    /api/v1/ontology/types/{id}
DELETE /api/v1/ontology/types/{id}
POST   /api/v1/ontology/types/{id}/properties
GET    /api/v1/ontology/properties/{id}
PUT    /api/v1/ontology/properties/{id}
DELETE /api/v1/ontology/properties/{id}
GET    /api/v1/ontology/links
POST   /api/v1/ontology/links
PUT    /api/v1/ontology/links/{id}
DELETE /api/v1/ontology/links/{id}
GET    /api/v1/ontology/graph
GET    /api/v1/ontology/types/{id}/objects   ?page&page_size&search&filter_json
GET    /api/v1/ontology/types/{id}/objects/{pk}
GET    /api/v1/ontology/types/{id}/objects/{pk}/links/{link_type_id}
GET    /api/v1/analytics/dashboards         ?page&page_size
POST   /api/v1/analytics/dashboards
GET    /api/v1/analytics/dashboards/{id}
PUT    /api/v1/analytics/dashboards/{id}
DELETE /api/v1/analytics/dashboards/{id}
POST   /api/v1/analytics/dashboards/{id}/widgets
PUT    /api/v1/analytics/widgets/{id}
DELETE /api/v1/analytics/widgets/{id}
POST   /api/v1/analytics/widgets/{id}/data
WS     /api/v1/ws/pipeline-runs/{run_id}    (after polling works)
```

**Removed from Phase 1:** `POST /analytics/dashboards/{id}/publish`, `GET /analytics/public/{token}`, `/public/$token` frontend route.

### Dataset ingestion (`POST /api/v1/datasets/ingest`)

Request:

```typescript
{
  source_id: string;
  table_or_file: string;
  dataset_name: string;
  display_name: string;
  mode: "create" | "overwrite";
}
```

Behavior:

1. Load source; 400 if soft-deleted or inactive
2. Decrypt config inside service only
3. Read via connector into PyArrow table
4. Create or overwrite Iceberg table
5. Register/update `datasets` (schema, row count, location, last_synced_at)
6. Write `lineage_events` (event_type `ingest`) + `lineage_event_inputs` (source)
7. Write `audit_events`
8. Return dataset record

---

## Compute Engine

```python
class ComputeEngine(Protocol):
    def query(self, sql: str) -> pa.Table: ...
    def read_iceberg(self, location: str) -> pa.Table: ...
    def write_iceberg(
        self, table: pa.Table, namespace: str, table_name: str, mode: str
    ) -> int | None: ...
    def profile(self, location: str) -> list[dict]: ...
```

**DuckDB Engine:**

- One connection per Celery worker process
- Load `iceberg` and `httpfs` extensions on startup
- S3 credentials from settings via `SET s3_*`
- `SET s3_url_style = 'path'` for MinIO
- `SELECT * FROM iceberg_scan('{location}', allow_moved_tables=true)`
- Writes: CTE query → Arrow → PyIceberg
- PyIceberg catalog: `sql` with Postgres URI
- Return `None` from `write_iceberg` when no new snapshot

**Spark Engine:** Stub; all methods raise `NotImplementedError` with message directing to DuckDB. Registered in `ENGINES` dict.

**Celery workers:** Use sync SQLAlchemy session (`CELERY_DATABASE_URL` psycopg2) while FastAPI uses async (see DECISIONS.md A2).

---

## Frontend Architecture

### App Shell

- Sidebar: 64px collapsed / 240px expanded
- Nav grows per BUILD_PLAN slice (Sources first, then Datasets, etc.)
- Top bar: "ATLAS", breadcrumb, user menu stub

### Design system

- Background: `zinc-950` / `zinc-900` / `zinc-800`
- Accent: `indigo-500` / `indigo-400` / `indigo-600`
- Success: `emerald-500` | Error: `red-500` | Warning: `amber-500`
- Text: `zinc-100` / `zinc-400` / `zinc-600`
- Borders: `zinc-700` / `zinc-600`
- Radius: `rounded-none` cards; `rounded-sm` buttons/badges
- Font: `font-mono` for data; `font-sans` for chrome
- No box shadows; borders only

### Routing (TanStack Router)

```
/                               → redirect /sources
/sources                        → SourcesPage
/sources/$id                    → SourceDetailPage
/datasets                       → DatasetsPage
/datasets/$id                   → DatasetDetailPage
/pipelines                      → PipelinesPage
/pipelines/$id                  → PipelineDetailPage
/pipelines/$id/builder          → PipelineBuilderPage
/lineage                        → LineagePage
/lineage/dataset/$id            → DatasetLineagePage
/ontology                       → OntologyPage
/ontology/types/$id             → ObjectTypeDetailPage
/workshop                       → WorkshopPage
/workshop/$id/edit              → DashboardBuilderPage
/workshop/$id/view              → DashboardViewerPage
```

### API layer

- One file per domain under `src/api/`
- TanStack Query hooks only from components
- Base URL from `VITE_API_URL`

### State

- **TanStack Query:** all server state
- **Zustand:** UI state only (`useLineageStore`, `useWorkshopStore`)

---

## Docker Compose & Configuration

See repository `docker-compose.yml` and `.env.example`. All values consumed via pydantic-settings. Localhost appears only in Compose and `.env`, never in application code.

---

## Project File Structure

```
atlas/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py, dependencies.py
│   │   ├── models/, schemas/, api/v1/, services/
│   │   ├── compute/, catalog/, connectors/, pipeline/, workers/
│   ├── tests/
│   ├── alembic/
│   ├── scripts/prove_iceberg_roundtrip.py
│   ├── requirements.txt, Dockerfile
├── frontend/
│   ├── src/api/, types/, stores/, components/, pages/
│   ├── package.json, vite.config.ts, tailwind.config.ts, tsconfig.json
├── docs/
│   ├── SPEC.md, BUILD_PLAN.md, DECISIONS.md
├── docker-compose.yml, .env.example, README.md
```

LineChartWidget and PieChartWidget files are not created in Phase 1.

---

## Code Conventions

### Backend

- Services contain all business logic; routes validate and delegate
- Async service methods; `async with db.begin():` for writes
- Never return ORM objects from services; use Pydantic schemas
- Audit writes on create, update, soft-delete, pipeline run
- Never log decrypted credentials
- SQLAlchemy 2.0 `select()` style
- Celery tasks are thin wrappers calling services
- Config via pydantic-settings only

### Frontend

- No direct axios in components
- TypeScript strict; no `any`
- React Flow: `fitView` on mount
- TanStack Virtual above 500 rows
- react-hook-form + zod for forms
- Skeleton loaders on async fetches
- Error boundaries on page components

### General

- UTC datetimes in API; local time in UI only
- UUIDs everywhere in API
- Soft deletes on mutable entities; append-only event tables exempt

---

## Phase 1 MVP Scope

Build end-to-end in BUILD_PLAN slice order. Do not start a later slice until acceptance checks pass.

| Slice | Deliverable |
|---|---|
| S01 | Infra, migrations, health, Iceberg round-trip proof |
| S02 | Sources API |
| S03 | Sources UI |
| S04 | Datasets API (ingest, preview, profile) |
| S05 | Datasets UI |
| S06 | Pipeline backend (validator, CTE, Celery, log polling) |
| S07 | Pipeline UI |
| S08 | Lineage API + UI |
| S09 | Ontology API + UI |
| S10 | Workshop dashboard CRUD |
| S11 | Table widget E2E |
| S12 | Metric card widget |
| S13 | Bar chart widget |
| S14 | Filter widget + layout save/load |
| S15 | Text widget |
| S16 | WebSocket pipeline logs |

### Deferred to Phase 2

Authentication, RBAC, scheduling, join/aggregate transforms, additional chart/filter widgets, link traversal UI, public sharing, `ontology_query` binding, additional connectors, Spark engine, audit UI, ClickHouse for high-concurrency serving, gating `derive` behind RBAC.
