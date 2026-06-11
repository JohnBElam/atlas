from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import pyarrow as pa
import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.iceberg_catalog import get_catalog
from app.compute.duckdb_engine import DuckDBEngine
from app.config import settings
from app.models.dataset import Dataset
from app.models.lineage import LineageEvent, LineageEventInput
from app.models.pipeline import PipelineDefinition, PipelineRun
from app.pipeline.transforms import build_pipeline_sql
from app.pipeline.validator import DagValidationError, validate_dag
LogFn = Callable[[str], None]


class PipelineExecutor:
    def __init__(self, db: Session, log_fn: LogFn | None = None) -> None:
        self._db = db
        self._log = log_fn or (lambda msg: None)
        self._engine = DuckDBEngine()

    def execute(self, run_id: uuid.UUID) -> None:
        run = self._db.get(PipelineRun, run_id)
        if run is None:
            raise ValueError(f"Pipeline run not found: {run_id}")

        pipeline = self._db.get(PipelineDefinition, run.pipeline_id)
        if pipeline is None or pipeline.deleted_at is not None:
            run.status = "failed"
            run.error_message = "Pipeline not found"
            run.completed_at = datetime.now(timezone.utc)
            self._db.commit()
            return

        try:
            self._log(f"Starting pipeline run {run_id}")
            run.status = "running"
            run.started_at = datetime.now(timezone.utc)
            self._db.commit()

            dag_json = pipeline.dag_json
            validate_dag(dag_json)

            dataset_locations = self._load_dataset_locations(dag_json)
            sql, params, output_config = build_pipeline_sql(dag_json, dataset_locations)
            self._log(f"Built SQL with {len(params)} parameters")

            result = self._execute_sql(sql, params)
            run.rows_read = result.num_rows
            self._log(f"Query returned {result.num_rows} rows")

            namespace = output_config.get("namespace", "default")
            table_name = output_config["table_name"]
            mode = output_config.get("mode", "overwrite")

            snapshot_id = self._engine.write_iceberg(result, namespace, table_name, mode)
            run.rows_written = result.num_rows
            run.iceberg_snapshot_id = snapshot_id
            self._log(f"Wrote to {namespace}.{table_name} (snapshot={snapshot_id})")

            target_dataset = self._upsert_output_dataset(
                namespace=namespace,
                table_name=table_name,
                mode=mode,
                result=result,
                pipeline=pipeline,
            )
            run.target_dataset_id = target_dataset.id

            self._write_lineage(
                run=run,
                target_dataset=target_dataset,
                dag_json=dag_json,
                snapshot_id=snapshot_id,
            )

            run.status = "success"
            run.completed_at = datetime.now(timezone.utc)
            self._db.commit()
            self._log("Pipeline run completed successfully")
        except Exception as exc:
            self._db.rollback()
            run = self._db.get(PipelineRun, run_id)
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.completed_at = datetime.now(timezone.utc)
                self._db.commit()
            self._log(f"Pipeline run failed: {exc}")
            raise
        finally:
            self._engine.close()

    def _execute_sql(self, sql: str, params: list[Any]) -> pa.Table:
        conn = self._engine._conn
        return conn.execute(sql, params).fetch_arrow_table()

    def _load_dataset_locations(self, dag_json: dict[str, Any]) -> dict[str, str]:
        dataset_ids: set[str] = set()
        for node in dag_json.get("nodes", []):
            if node.get("type") == "source" and node.get("dataset_id"):
                dataset_ids.add(str(node["dataset_id"]))

        locations: dict[str, str] = {}
        for ds_id in dataset_ids:
            dataset = self._db.get(Dataset, uuid.UUID(ds_id))
            if dataset is None or dataset.deleted_at is not None:
                raise DagValidationError(f"Dataset not found: {ds_id}")
            locations[ds_id] = dataset.iceberg_location
        return locations

    def _upsert_output_dataset(
        self,
        *,
        namespace: str,
        table_name: str,
        mode: str,
        result: pa.Table,
        pipeline: PipelineDefinition,
    ) -> Dataset:
        catalog = get_catalog()
        iceberg_table = catalog.load_table(f"{namespace}.{table_name}")
        location = iceberg_table.location()

        schema_json = {
            "fields": [
                {"name": f.name, "type": str(f.type)} for f in result.schema
            ]
        }
        now = datetime.now(timezone.utc)

        stmt = select(Dataset).where(
            Dataset.iceberg_namespace == namespace,
            Dataset.iceberg_table == table_name,
            Dataset.deleted_at.is_(None),
        )
        existing = self._db.execute(stmt).scalar_one_or_none()

        if existing and mode == "overwrite":
            existing.iceberg_location = location
            existing.schema_json = schema_json
            existing.row_count = result.num_rows
            existing.last_synced_at = now
            existing.updated_at = now
            self._db.flush()
            return existing

        if existing:
            return existing

        dataset = Dataset(
            name=table_name,
            display_name=table_name.replace("_", " ").title(),
            iceberg_namespace=namespace,
            iceberg_table=table_name,
            iceberg_location=location,
            schema_json=schema_json,
            row_count=result.num_rows,
            last_synced_at=now,
        )
        self._db.add(dataset)
        self._db.flush()
        return dataset

    def _write_lineage(
        self,
        *,
        run: PipelineRun,
        target_dataset: Dataset,
        dag_json: dict[str, Any],
        snapshot_id: int | None,
    ) -> None:
        event = LineageEvent(
            event_type="transform",
            target_dataset_id=target_dataset.id,
            pipeline_run_id=run.id,
            iceberg_snapshot_id=snapshot_id,
            transform_summary=f"Pipeline {run.pipeline_id}",
        )
        self._db.add(event)
        self._db.flush()

        for node in dag_json.get("nodes", []):
            if node.get("type") == "source" and node.get("dataset_id"):
                self._db.add(
                    LineageEventInput(
                        lineage_event_id=event.id,
                        input_type="dataset",
                        dataset_id=uuid.UUID(str(node["dataset_id"])),
                    )
                )


def append_run_log(run_id: uuid.UUID, message: str) -> None:
    client = redis.from_url(settings.redis_url)
    client.rpush(f"pipeline:logs:{run_id}", message)


def get_run_logs(run_id: uuid.UUID, since: int = 0) -> tuple[list[str], int]:
    client = redis.from_url(settings.redis_url)
    key = f"pipeline:logs:{run_id}"
    lines = client.lrange(key, since, -1)
    decoded = [line.decode() if isinstance(line, bytes) else str(line) for line in lines]
    next_since = since + len(decoded)
    return decoded, next_since
