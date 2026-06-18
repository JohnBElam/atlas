from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.pipeline import PipelineRunResponse
from app.services.pipeline_service import PipelineService, RunNotFoundError

client = TestClient(app)


def _run_response(*, run_id: uuid.UUID, status: str = "running") -> PipelineRunResponse:
    now = datetime.now(timezone.utc)
    pipeline_id = uuid.uuid4()
    return PipelineRunResponse(
        id=run_id,
        pipeline_id=pipeline_id,
        status=status,
        triggered_by="manual",
        celery_task_id=None,
        started_at=now,
        completed_at=None,
        rows_read=None,
        rows_written=None,
        target_dataset_id=None,
        iceberg_snapshot_id=None,
        error_message=None,
        created_at=now,
    )


def test_ws_unknown_run_closes_with_error() -> None:
    run_id = uuid.uuid4()
    with patch.object(
        PipelineService,
        "get_run",
        AsyncMock(side_effect=RunNotFoundError("Pipeline run not found")),
    ):
        with client.websocket_connect(f"/api/v1/ws/pipeline-runs/{run_id}") as ws:
            msg = ws.receive_json()
            assert msg == {"error": "Pipeline run not found"}


def test_ws_streams_incremental_log_lines() -> None:
    run_id = uuid.uuid4()
    log_batches = [
        (["line 1"], 1),
        (["line 2"], 2),
        ([], 2),
        ([], 2),
    ]
    batch_index = {"i": 0}

    def fake_get_run_logs(_run_id: uuid.UUID, since: int = 0) -> tuple[list[str], int]:
        idx = batch_index["i"]
        if idx < len(log_batches):
            batch_index["i"] += 1
            return log_batches[idx]
        return [], since

    get_run_calls = {"n": 0}

    async def fake_get_run(
        _self: object, _db: object, _run_id: uuid.UUID
    ) -> PipelineRunResponse:
        get_run_calls["n"] += 1
        status = "running" if get_run_calls["n"] <= 4 else "success"
        return _run_response(run_id=run_id, status=status)

    with (
        patch.object(PipelineService, "get_run", fake_get_run),
        patch("app.api.v1.ws.get_run_logs", side_effect=fake_get_run_logs),
        patch("app.api.v1.ws._IDLE_POLLS_BEFORE_DONE", 2),
        patch("app.api.v1.ws._POLL_INTERVAL_SEC", 0),
    ):
        with client.websocket_connect(f"/api/v1/ws/pipeline-runs/{run_id}") as ws:
            first = ws.receive_json()
            assert first == {"lines": ["line 1"], "next_since": 1}
            second = ws.receive_json()
            assert second == {"lines": ["line 2"], "next_since": 2}
            done = ws.receive_json()
            assert done == {"type": "done"}
