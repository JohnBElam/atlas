from __future__ import annotations

from typing import Protocol
from uuid import UUID

import pyarrow as pa

from app.connectors.types import ColumnDef


class Connector(Protocol):
    def test_connection(self) -> bool: ...

    def list_tables(self) -> list[str]: ...

    def get_schema(self, table: str) -> list[ColumnDef]: ...

    def read_table(self, table: str, limit: int | None) -> pa.Table: ...


def get_connector(source_type: str, source_id: UUID, config: dict) -> Connector:
    from app.connectors.csv_connector import CsvConnector
    from app.connectors.parquet_connector import ParquetConnector
    from app.connectors.postgres_connector import PostgresConnector
    from app.connectors.stub_connectors import (
        BigQueryConnector,
        KafkaConnector,
        MySQLConnector,
        RestApiConnector,
        S3Connector,
        SnowflakeConnector,
    )
    from app.schemas.source import SourceType

    connector_classes: dict[str, type] = {
        SourceType.CSV: CsvConnector,
        SourceType.PARQUET: ParquetConnector,
        SourceType.POSTGRESQL: PostgresConnector,
        SourceType.MYSQL: MySQLConnector,
        SourceType.S3: S3Connector,
        SourceType.SNOWFLAKE: SnowflakeConnector,
        SourceType.BIGQUERY: BigQueryConnector,
        SourceType.REST_API: RestApiConnector,
        SourceType.KAFKA: KafkaConnector,
    }
    connector_cls = connector_classes.get(source_type)
    if connector_cls is None:
        raise ValueError(f"Unknown source type: {source_type}")
    return connector_cls(source_id=source_id, config=config)
