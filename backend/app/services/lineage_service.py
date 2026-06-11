from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset import Dataset
from app.models.lineage import LineageEvent, LineageEventInput
from app.models.pipeline import PipelineDefinition, PipelineRun
from app.models.source import DataSource
from app.schemas.lineage import (
    LineageGraphEdge,
    LineageGraphNode,
    LineageGraphResponse,
    LineageNodeData,
    SnapshotHistoryItem,
)


class LineageNotFoundError(Exception):
    pass


class LineageService:
    async def record_ingest(
        self,
        db: AsyncSession,
        *,
        target_dataset_id: uuid.UUID,
        source_id: uuid.UUID,
        iceberg_snapshot_id: int | None = None,
    ) -> LineageEvent:
        event = LineageEvent(
            event_type="ingest",
            target_dataset_id=target_dataset_id,
            iceberg_snapshot_id=iceberg_snapshot_id,
            transform_summary="Ingest from source",
        )
        db.add(event)
        await db.flush()
        db.add(
            LineageEventInput(
                lineage_event_id=event.id,
                input_type="source",
                source_id=source_id,
            )
        )
        return event

    async def get_full_graph(self, db: AsyncSession) -> LineageGraphResponse:
        events_stmt = select(LineageEvent).where(LineageEvent.deleted_at.is_(None))
        events = (await db.execute(events_stmt)).scalars().all()

        nodes_map: dict[str, LineageGraphNode] = {}
        edges: list[LineageGraphEdge] = []
        edge_counter = 0

        dataset_ids: set[uuid.UUID] = set()
        source_ids: set[uuid.UUID] = set()
        pipeline_ids: set[uuid.UUID] = set()

        for event in events:
            dataset_ids.add(event.target_dataset_id)
            if event.pipeline_run_id:
                run = await db.get(PipelineRun, event.pipeline_run_id)
                if run:
                    pipeline_ids.add(run.pipeline_id)

            inputs_stmt = select(LineageEventInput).where(
                LineageEventInput.lineage_event_id == event.id
            )
            inputs = (await db.execute(inputs_stmt)).scalars().all()
            for inp in inputs:
                if inp.source_id:
                    source_ids.add(inp.source_id)
                if inp.dataset_id:
                    dataset_ids.add(inp.dataset_id)

        pos_x = 0.0
        for ds_id in dataset_ids:
            dataset = await db.get(Dataset, ds_id)
            if dataset and dataset.deleted_at is None:
                node_id = f"dataset-{ds_id}"
                nodes_map[node_id] = LineageGraphNode(
                    id=node_id,
                    position={"x": pos_x, "y": 100},
                    data=LineageNodeData(
                        id=node_id,
                        label=dataset.display_name,
                        node_type="dataset",
                        entity_id=ds_id,
                        row_count=dataset.row_count,
                        last_updated=dataset.updated_at,
                    ),
                )
                pos_x += 250

        pos_x = 0.0
        for src_id in source_ids:
            source = await db.get(DataSource, src_id)
            if source and source.deleted_at is None:
                node_id = f"source-{src_id}"
                nodes_map[node_id] = LineageGraphNode(
                    id=node_id,
                    position={"x": pos_x, "y": 0},
                    data=LineageNodeData(
                        id=node_id,
                        label=source.name,
                        node_type="source",
                        entity_id=src_id,
                        connector_type=source.source_type,
                        last_updated=source.updated_at,
                    ),
                )
                pos_x += 250

        pos_x = 0.0
        for pl_id in pipeline_ids:
            pipeline = await db.get(PipelineDefinition, pl_id)
            if pipeline and pipeline.deleted_at is None:
                node_id = f"pipeline-{pl_id}"
                last_run_stmt = (
                    select(PipelineRun)
                    .where(PipelineRun.pipeline_id == pl_id)
                    .order_by(PipelineRun.created_at.desc())
                    .limit(1)
                )
                last_run = (await db.execute(last_run_stmt)).scalar_one_or_none()
                nodes_map[node_id] = LineageGraphNode(
                    id=node_id,
                    position={"x": pos_x, "y": 200},
                    data=LineageNodeData(
                        id=node_id,
                        label=pipeline.name,
                        node_type="pipeline",
                        entity_id=pl_id,
                        last_run_status=last_run.status if last_run else None,
                        last_updated=pipeline.updated_at,
                    ),
                )
                pos_x += 250

        for event in events:
            target_node = f"dataset-{event.target_dataset_id}"
            if event.pipeline_run_id:
                run = await db.get(PipelineRun, event.pipeline_run_id)
                if run:
                    pipeline_node = f"pipeline-{run.pipeline_id}"
                    pipeline = await db.get(PipelineDefinition, run.pipeline_id)
                    label = pipeline.name if pipeline else "Pipeline"
                    if pipeline_node in nodes_map and target_node in nodes_map:
                        edge_counter += 1
                        edges.append(
                            LineageGraphEdge(
                                id=f"edge-{edge_counter}",
                                source=pipeline_node,
                                target=target_node,
                                label=label,
                            )
                        )

            inputs_stmt = select(LineageEventInput).where(
                LineageEventInput.lineage_event_id == event.id
            )
            inputs = (await db.execute(inputs_stmt)).scalars().all()
            for inp in inputs:
                if inp.source_id:
                    src_node = f"source-{inp.source_id}"
                    if event.pipeline_run_id:
                        run = await db.get(PipelineRun, event.pipeline_run_id)
                        if run:
                            pl_node = f"pipeline-{run.pipeline_id}"
                            if src_node in nodes_map and pl_node in nodes_map:
                                edge_counter += 1
                                edges.append(
                                    LineageGraphEdge(
                                        id=f"edge-{edge_counter}",
                                        source=src_node,
                                        target=pl_node,
                                        label="ingest",
                                    )
                                )
                    elif target_node in nodes_map and src_node in nodes_map:
                        edge_counter += 1
                        edges.append(
                            LineageGraphEdge(
                                id=f"edge-{edge_counter}",
                                source=src_node,
                                target=target_node,
                                label="ingest",
                            )
                        )
                if inp.dataset_id and event.pipeline_run_id:
                    ds_node = f"dataset-{inp.dataset_id}"
                    run = await db.get(PipelineRun, event.pipeline_run_id)
                    if run:
                        pl_node = f"pipeline-{run.pipeline_id}"
                        if ds_node in nodes_map and pl_node in nodes_map:
                            edge_counter += 1
                            edges.append(
                                LineageGraphEdge(
                                    id=f"edge-{edge_counter}",
                                    source=ds_node,
                                    target=pl_node,
                                    label="input",
                                )
                            )

        return LineageGraphResponse(
            nodes=list(nodes_map.values()),
            edges=edges,
        )

    async def get_dataset_subgraph(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
        hops: int = 3,
    ) -> LineageGraphResponse:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None or dataset.deleted_at is not None:
            raise LineageNotFoundError("Dataset not found")

        full_graph = await self.get_full_graph(db)
        center = f"dataset-{dataset_id}"
        if center not in {n.id for n in full_graph.nodes}:
            return LineageGraphResponse(nodes=[], edges=[])

        connected: set[str] = {center}
        for _ in range(hops):
            new_nodes: set[str] = set()
            for edge in full_graph.edges:
                if edge.source in connected:
                    new_nodes.add(edge.target)
                if edge.target in connected:
                    new_nodes.add(edge.source)
            connected |= new_nodes

        nodes = [n for n in full_graph.nodes if n.id in connected]
        edges = [
            e
            for e in full_graph.edges
            if e.source in connected and e.target in connected
        ]
        return LineageGraphResponse(nodes=nodes, edges=edges)

    async def get_snapshot_history(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> list[SnapshotHistoryItem]:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None or dataset.deleted_at is not None:
            raise LineageNotFoundError("Dataset not found")

        try:
            from app.catalog.iceberg_catalog import get_catalog

            catalog = get_catalog()
            table = catalog.load_table(f"{dataset.iceberg_namespace}.{dataset.iceberg_table}")
            snapshots = []
            for snap in table.snapshots():
                snapshots.append(
                    SnapshotHistoryItem(
                        snapshot_id=snap.snapshot_id,
                        committed_at=datetime.fromtimestamp(
                            snap.timestamp_ms / 1000, tz=datetime.now().astimezone().tzinfo
                        )
                        if snap.timestamp_ms
                        else None,
                        summary=str(snap.summary) if snap.summary else None,
                    )
                )
            return snapshots
        except Exception:
            return []

    async def get_dataset_detail(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> dict[str, Any]:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None or dataset.deleted_at is not None:
            raise LineageNotFoundError("Dataset not found")

        runs_stmt = (
            select(PipelineRun)
            .where(PipelineRun.target_dataset_id == dataset_id)
            .order_by(PipelineRun.created_at.desc())
            .limit(5)
        )
        runs = (await db.execute(runs_stmt)).scalars().all()
        snapshots = await self.get_snapshot_history(db, dataset_id)

        return {
            "dataset": dataset,
            "recent_runs": runs,
            "snapshots": snapshots,
        }
