from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.pipeline.executor import get_run_logs
from app.services.pipeline_service import PipelineService, RunNotFoundError

router = APIRouter(prefix="/ws", tags=["websocket"])

_TERMINAL_STATUSES = frozenset({"success", "failed", "cancelled"})
_IDLE_POLLS_BEFORE_DONE = 4
_POLL_INTERVAL_SEC = 0.5


def _pipeline_service() -> PipelineService:
    return PipelineService()


@router.websocket("/pipeline-runs/{run_id}")
async def pipeline_run_logs(
    websocket: WebSocket,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: PipelineService = Depends(_pipeline_service),
) -> None:
    await websocket.accept()

    try:
        run = await service.get_run(db, run_id)
    except RunNotFoundError:
        await websocket.send_json({"error": "Pipeline run not found"})
        await websocket.close(code=4404)
        return

    since = 0
    idle_polls = 0

    try:
        while True:
            lines, next_since = get_run_logs(run_id, since=since)
            if lines:
                await websocket.send_json({"lines": lines, "next_since": next_since})
                since = next_since
                idle_polls = 0
            else:
                idle_polls += 1

            run = await service.get_run(db, run_id)
            if run.status in _TERMINAL_STATUSES and idle_polls >= _IDLE_POLLS_BEFORE_DONE:
                await websocket.send_json({"type": "done"})
                break

            await asyncio.sleep(_POLL_INTERVAL_SEC)
    except WebSocketDisconnect:
        return
