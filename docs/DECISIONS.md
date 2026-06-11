# ATLAS Decision Log

Architecture decisions for Phase 1. Format: **Decision** | Rationale | Defers | Protects

When the spec is ambiguous, the smallest defensible assumption is recorded under [Assumptions flagged for review](#assumptions-flagged-for-review).

Related: [`SPEC.md`](SPEC.md) | [`BUILD_PLAN.md`](BUILD_PLAN.md)

---

## D01 — Lineage events as system of record

| | |
|---|---|
| **Decision** | The lineage graph is built exclusively from `lineage_events` and `lineage_event_inputs`. Iceberg snapshots attach as optional evidence (`iceberg_snapshot_id` nullable). |
| **Rationale** | Snapshots record table state, not pipeline intent or cross-entity semantics. Automatic lineage must not require user annotation. |
| **Defers** | Shortcuts that infer lineage from `table.history()` alone |
| **Protects** | Correct source→pipeline→dataset semantics at scale; commercial audit story |

---

## D02 — Tenancy columns now, tenancy features later

| | |
|---|---|
| **Decision** | Every major mutable table includes `organization_id UUID NULL` and `created_by UUID NULL` from the first migration. Phase 1 logic never reads or writes them. |
| **Rationale** | Commercial multi-tenant deployment must not require schema migration against live customer data. |
| **Defers** | Auth, users, org scoping, RBAC |
| **Protects** | Customer data model stability; licensing to multiple orgs |

---

## D03 — Audit events now, audit UI later

| | |
|---|---|
| **Decision** | `audit_events` table written from the service layer on create, update, soft-delete, and pipeline run. `actor` is NULL in Phase 1. No audit viewer. |
| **Rationale** | Auditability is part of the product value proposition; history must accumulate from day one. |
| **Defers** | Audit UI, actor identity, export |
| **Protects** | Compliance and operational forensics for licensed deployments |

---

## D04 — ComputeEngine protocol; DuckDB only in Phase 1

| | |
|---|---|
| **Decision** | All pipeline and query execution goes through `ComputeEngine`. `DuckDBEngine` is the only implementation. `SparkEngine` is a registered stub raising `NotImplementedError`. |
| **Rationale** | Phase 1 is single-node local; the seam allows Spark/Trino later without rewriting services. |
| **Defers** | Spark, Trino, ClickHouse engine implementations |
| **Protects** | Distributed compute as a plug-in, not a rewrite |

---

## D05 — Derive transform with DuckDB SQL expressions

| | |
|---|---|
| **Decision** | `derive` nodes accept arbitrary DuckDB scalar SQL expressions in Phase 1. Expressions validated (no statements, no semicolons). Identifier sanitization and parameterization still mandatory in CTE builder. |
| **Rationale** | Single-user local tool; operator runs SQL against their own data. Expressiveness unblocks real pipelines. |
| **Defers** | RBAC gating on `derive` when multi-user lands |
| **Protects** | Pipeline expressiveness in Phase 1; security path defined for Phase 2 |

---

## D06 — Parquet upload in Phase 1

| | |
|---|---|
| **Decision** | Parquet file upload and ingestion supported alongside CSV via PyArrow. |
| **Rationale** | PyArrow reads Parquet with minimal additional code; common enterprise format. |
| **Defers** | Nothing |
| **Protects** | File ingestion parity for client deployments |

---

## D07 — Pipeline node scope without join/aggregate

| | |
|---|---|
| **Decision** | Phase 1 implements: source, filter, select, rename, cast, derive, sort, limit, deduplicate, output. Join and aggregate config formats documented but not implemented. |
| **Rationale** | Shippable DAG executor and CTE builder; joins/aggregates significantly increase validation and SQL complexity. |
| **Defers** | Join and aggregate nodes, multi-input CTE patterns |
| **Protects** | CTE correctness and on-time Phase 1 delivery |

---

## D08 — Ontology resolution: primary key, no inference

| | |
|---|---|
| **Decision** | Object browsing requires `primary_key_property_id`. Multi-dataset object types supported only when every backing dataset maps the PK column; explicit join on PK. No join inference. Violations return HTTP 400. |
| **Rationale** | Loud failures beat silent partial or wrong results in a semantic layer. |
| **Defers** | Automatic join inference, fuzzy matching |
| **Protects** | Trust in object browser and licensed ontology workflows |

---

## D09 — Workshop widget build order

| | |
|---|---|
| **Decision** | Build Workshop widgets strictly: Dashboard CRUD → table → metric_card → bar_chart → dropdown filter → layout save/load → text. |
| **Rationale** | Table widget proves binding → query → render; later widgets reuse the same data path. |
| **Defers** | Charts and filters before table E2E |
| **Protects** | Incremental, verifiable Workshop delivery |

---

## D10 — Append-only run, audit, and lineage input tables

| | |
|---|---|
| **Decision** | `pipeline_runs`, `lineage_event_inputs`, and `audit_events` have no `deleted_at` and no DELETE API in Phase 1. `lineage_events` retains `deleted_at` for rare administrative correction. |
| **Rationale** | Operational and audit history must be immutable; soft-deleting runs would undermine lineage integrity. |
| **Defers** | Soft-delete on run records, run purging |
| **Protects** | Audit integrity and reproducible lineage |

---

## D11 — HTTP log polling before WebSocket

| | |
|---|---|
| **Decision** | Pipeline run logs delivered via Redis list + `GET /pipelines/runs/{run_id}/logs?since=0` first. WebSocket at `/ws/pipeline-runs/{run_id}` only after polling works end-to-end. |
| **Rationale** | De-risk Celery + Redis + API before adding connection lifecycle complexity. |
| **Defers** | Real-time log streaming as first delivery mechanism |
| **Protects** | Reliable run debugging in Phase 1 |

---

## D12 — Future scale as design constraint, not Phase 1 claim

| | |
|---|---|
| **Decision** | End-state product targets billions of rows queryable, thousands of users, and hundreds of connector types. Phase 1 targets single-user, single-node DuckDB (thousands–millions of rows in practice). Abstractions must not block scale-up. |
| **Rationale** | Two-person team must ship Phase 1 while preserving commercial credibility and expansion path. |
| **Defers** | Performance claims, distributed execution, connector catalog, multi-tenancy features |
| **Protects** | Architecture credibility with licensees and dogfood deployments |

---

## Assumptions flagged for review

These are the smallest defensible choices where the spec did not fully pin behavior. Confirm or revise before dependent slices ship.

### A1 — lineage_events soft-delete without cascading to inputs

**Assumption:** `lineage_events.deleted_at` allows administrative hiding of an event from graph queries. `lineage_event_inputs` rows are never soft-deleted. Service layer prevents orphan inputs when soft-deleting an event (e.g., reject or soft-delete event only when policy allows).

**Review before:** S08 (Lineage UI)

### A2 — Async API, sync Celery database sessions

**Assumption:** FastAPI uses `DATABASE_URL` with `asyncpg` and async SQLAlchemy. Celery workers use `CELERY_DATABASE_URL` with `psycopg2` and sync sessions to avoid event-loop and async-session lifecycle issues in forked workers.

**Review before:** S06 (Pipeline backend)

### A3 — File source list_tables from MinIO prefix

**Assumption:** For CSV/Parquet sources, `Connector.list_tables()` returns filenames under `atlas-data/uploads/{source_id}/` in MinIO, not local filesystem paths.

**Review before:** S02 (Sources API)

### A4 — Cross-widget filter merge semantics

**Assumption:** Filter widget `applies_to` holds target widget UUIDs. Active filter values merge into data queries as: **AND across filter widgets**, **OR within a single filter widget's multi-select** (when `multi_select: true`).

**Review before:** S14 (Filter + layout)

### A5 — Primary key set after properties via type update

**Assumption:** `primary_key_property_id` is set via `PUT /api/v1/ontology/types/{id}` after properties exist, using the deferrable FK on `object_types`. Creation flow: create type → add properties → set PK on type.

**Review before:** S09 (Ontology)

---

## Change log

| Date | Change |
|------|--------|
| 2026-06-09 | Initial seed from Phase 1 planning session (D01–D12, A1–A5) |
