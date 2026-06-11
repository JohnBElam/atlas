from __future__ import annotations

from uuid import UUID

import psycopg2
import pyarrow as pa
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from app.connectors.types import ColumnDef


def _pg_type_to_atlas(pg_type: str) -> str:
    mapping = {
        "character varying": "string",
        "varchar": "string",
        "text": "string",
        "char": "string",
        "integer": "integer",
        "bigint": "integer",
        "smallint": "integer",
        "numeric": "float",
        "double precision": "float",
        "real": "float",
        "boolean": "boolean",
        "date": "date",
        "timestamp without time zone": "timestamp",
        "timestamp with time zone": "timestamp",
        "json": "json",
        "jsonb": "json",
    }
    return mapping.get(pg_type, pg_type)


class PostgresConnector:
    def __init__(self, source_id: UUID, config: dict) -> None:
        self.source_id = source_id
        self.config = config
        self._connection_string = config.get("connection_string", "")

    def _connect(self):
        if not self._connection_string:
            raise ValueError("PostgreSQL connection_string is required")
        return psycopg2.connect(self._connection_string)

    def test_connection(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True

    def list_tables(self) -> list[str]:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]

    def get_schema(self, table: str) -> list[ColumnDef]:
        if not table.replace("_", "").isalnum():
            raise ValueError("Invalid table name")
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_name = %s
            ORDER BY ordinal_position
        """
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (table,))
                rows = cur.fetchall()
                if not rows:
                    raise ValueError(f"Table not found: {table}")
                return [
                    ColumnDef(
                        name=row["column_name"],
                        type=_pg_type_to_atlas(row["data_type"]),
                        nullable=row["is_nullable"] == "YES",
                    )
                    for row in rows
                ]

    def read_table(self, table: str, limit: int | None) -> pa.Table:
        if not table.replace("_", "").isalnum():
            raise ValueError("Invalid table name")
        with self._connect() as conn:
            with conn.cursor() as cur:
                query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                if limit is not None:
                    query = sql.SQL("{} LIMIT %s").format(query)
                    cur.execute(query, (limit,))
                else:
                    cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        return pa.Table.from_pydict(
            {col: [row[i] for row in rows] for i, col in enumerate(columns)}
        )
