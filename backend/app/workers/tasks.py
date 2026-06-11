from __future__ import annotations

import uuid

from app.database_sync import get_sync_db
from app.pipeline.executor import PipelineExecutor, append_run_log
from app.workers.celery_app import celery_app


@celery_app.task(name="run_pipeline")
def run_pipeline_task(run_id: str) -> None:
    run_uuid = uuid.UUID(run_id)
    db = get_sync_db()
    try:

        def log_fn(message: str) -> None:
            append_run_log(run_uuid, message)

        executor = PipelineExecutor(db, log_fn=log_fn)
        executor.execute(run_uuid)
    finally:
        db.close()
