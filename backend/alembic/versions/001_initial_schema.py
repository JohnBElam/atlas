"""Initial ATLAS schema per SPEC.md

Revision ID: 001
Revises:
Create Date: 2026-06-09

"""

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_data_sources_deleted_at ON data_sources(deleted_at)")
    op.execute("CREATE INDEX idx_data_sources_source_type ON data_sources(source_type)")
    op.execute(
        "CREATE UNIQUE INDEX uq_data_sources_name_active ON data_sources(name) WHERE deleted_at IS NULL"
    )

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_datasets_deleted_at ON datasets(deleted_at)")
    op.execute("CREATE INDEX idx_datasets_source_id ON datasets(source_id)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_pipeline_definitions_deleted_at ON pipeline_definitions(deleted_at)")
    op.execute(
        "CREATE UNIQUE INDEX uq_pipeline_definitions_name_active ON pipeline_definitions(name) WHERE deleted_at IS NULL"
    )

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_pipeline_runs_pipeline_id ON pipeline_runs(pipeline_id)")
    op.execute("CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status)")
    op.execute("CREATE INDEX idx_pipeline_runs_created_at ON pipeline_runs(created_at)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_lineage_events_target ON lineage_events(target_dataset_id)")
    op.execute("CREATE INDEX idx_lineage_events_run ON lineage_events(pipeline_run_id)")
    op.execute("CREATE INDEX idx_lineage_events_deleted_at ON lineage_events(deleted_at)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_lineage_event_inputs_event ON lineage_event_inputs(lineage_event_id)")
    op.execute("CREATE INDEX idx_lineage_event_inputs_dataset ON lineage_event_inputs(dataset_id)")
    op.execute("CREATE INDEX idx_lineage_event_inputs_source ON lineage_event_inputs(source_id)")

    op.execute("""
        CREATE TABLE audit_events (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID,
          actor UUID,
          action TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id UUID NOT NULL,
          payload JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id)")
    op.execute("CREATE INDEX idx_audit_events_created_at ON audit_events(created_at)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_object_types_deleted_at ON object_types(deleted_at)")
    op.execute(
        "CREATE UNIQUE INDEX uq_object_types_name_active ON object_types(name) WHERE deleted_at IS NULL"
    )

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_object_properties_type ON object_properties(object_type_id)")
    op.execute("CREATE INDEX idx_object_properties_deleted_at ON object_properties(deleted_at)")
    op.execute(
        "CREATE UNIQUE INDEX uq_object_properties_name_active ON object_properties(object_type_id, name) WHERE deleted_at IS NULL"
    )

    op.execute("""
        ALTER TABLE object_types
          ADD CONSTRAINT fk_primary_key_property
          FOREIGN KEY (primary_key_property_id) REFERENCES object_properties(id)
          DEFERRABLE INITIALLY DEFERRED
    """)

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_link_types_deleted_at ON link_types(deleted_at)")
    op.execute(
        "CREATE UNIQUE INDEX uq_link_types_name_active ON link_types(name) WHERE deleted_at IS NULL"
    )

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_dashboards_deleted_at ON dashboards(deleted_at)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_widgets_dashboard_id ON widgets(dashboard_id)")
    op.execute("CREATE INDEX idx_widgets_deleted_at ON widgets(deleted_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS widgets")
    op.execute("DROP TABLE IF EXISTS dashboards")
    op.execute("DROP TABLE IF EXISTS link_types")
    op.execute("ALTER TABLE object_types DROP CONSTRAINT IF EXISTS fk_primary_key_property")
    op.execute("DROP TABLE IF EXISTS object_properties")
    op.execute("DROP TABLE IF EXISTS object_types")
    op.execute("DROP TABLE IF EXISTS audit_events")
    op.execute("DROP TABLE IF EXISTS lineage_event_inputs")
    op.execute("DROP TABLE IF EXISTS lineage_events")
    op.execute("DROP TABLE IF EXISTS pipeline_runs")
    op.execute("DROP TABLE IF EXISTS pipeline_definitions")
    op.execute("DROP TABLE IF EXISTS datasets")
    op.execute("DROP TABLE IF EXISTS data_sources")
