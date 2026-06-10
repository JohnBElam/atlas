from __future__ import annotations

import io
from uuid import UUID

import pyarrow as pa
import pyarrow.parquet as pq

from app.connectors.types import ColumnDef
from app.connectors.csv_connector import _arrow_type_name
from app.storage.minio import get_minio_storage


class ParquetConnector:
    def __init__(self, source_id: UUID, config: dict) -> None:
        self.source_id = source_id
        self.config = config
        self._storage = get_minio_storage()

    def test_connection(self) -> bool:
        return True

    def list_tables(self) -> list[str]:
        return self._storage.list_filenames(self.source_id)

    def get_schema(self, table: str) -> list[ColumnDef]:
        data = self._storage.download_file(self.source_id, table)
        schema = pq.read_schema(io.BytesIO(data))
        return [
            ColumnDef(
                name=field.name,
                type=_arrow_type_name(field),
                nullable=field.nullable,
            )
            for field in schema
        ]

    def read_table(self, table: str, limit: int | None) -> pa.Table:
        data = self._storage.download_file(self.source_id, table)
        arrow_table = pq.read_table(io.BytesIO(data))
        if limit is not None:
            return arrow_table.slice(0, limit)
        return arrow_table
