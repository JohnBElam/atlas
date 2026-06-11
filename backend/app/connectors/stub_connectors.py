from __future__ import annotations

from uuid import UUID

import pyarrow as pa

from app.connectors.types import ColumnDef


class _StubConnector:
    _connector_name: str = "unknown"

    def __init__(self, source_id: UUID, config: dict) -> None:
        self.source_id = source_id
        self.config = config

    def _not_implemented(self) -> None:
        raise NotImplementedError(f"{self._connector_name} connector is not implemented in Phase 1")

    def test_connection(self) -> bool:
        self._not_implemented()
        return False

    def list_tables(self) -> list[str]:
        self._not_implemented()
        return []

    def get_schema(self, table: str) -> list[ColumnDef]:
        self._not_implemented()
        return []

    def read_table(self, table: str, limit: int | None) -> pa.Table:
        self._not_implemented()
        return pa.table({})


class MySQLConnector(_StubConnector):
    _connector_name = "MySQL"


class S3Connector(_StubConnector):
    _connector_name = "S3"


class SnowflakeConnector(_StubConnector):
    _connector_name = "Snowflake"


class BigQueryConnector(_StubConnector):
    _connector_name = "BigQuery"


class RestApiConnector(_StubConnector):
    _connector_name = "REST API"


class KafkaConnector(_StubConnector):
    _connector_name = "Kafka"
