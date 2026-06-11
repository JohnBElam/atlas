from __future__ import annotations

import duckdb
import pyarrow as pa
from pyiceberg.exceptions import NoSuchTableError

from app.catalog.iceberg_catalog import get_catalog
from app.config import settings


class DuckDBEngine:
    def __init__(self) -> None:
        self._conn = duckdb.connect()
        self._load_extensions()
        self._configure_s3()

    def _load_extensions(self) -> None:
        self._conn.execute("INSTALL iceberg")
        self._conn.execute("LOAD iceberg")
        self._conn.execute("INSTALL httpfs")
        self._conn.execute("LOAD httpfs")

    def _configure_s3(self) -> None:
        self._conn.execute(f"SET s3_endpoint='{settings.minio_endpoint}'")
        self._conn.execute(f"SET s3_access_key_id='{settings.minio_access_key}'")
        self._conn.execute(f"SET s3_secret_access_key='{settings.minio_secret_key}'")
        self._conn.execute(f"SET s3_use_ssl={str(settings.s3_use_ssl).lower()}")
        self._conn.execute("SET s3_url_style='path'")
        self._conn.execute("SET unsafe_enable_version_guessing=true")

    def query(self, sql: str) -> pa.Table:
        return self._conn.execute(sql).fetch_arrow_table()

    def read_iceberg(self, location: str) -> pa.Table:
        return self._conn.execute(
            "SELECT * FROM iceberg_scan(?, allow_moved_paths=true)",
            [location],
        ).fetch_arrow_table()

    def write_iceberg(
        self,
        table: pa.Table,
        namespace: str,
        table_name: str,
        mode: str,
    ) -> int | None:
        catalog = get_catalog()
        identifier = f"{namespace}.{table_name}"

        catalog.create_namespace_if_not_exists(namespace)

        try:
            iceberg_table = catalog.load_table(identifier)
        except NoSuchTableError:
            iceberg_table = catalog.create_table(identifier, schema=table.schema)

        if mode == "overwrite":
            iceberg_table.overwrite(table)
        elif mode == "append":
            iceberg_table.append(table)
        else:
            raise ValueError(f"Unsupported write mode: {mode}")

        snapshot = iceberg_table.current_snapshot()
        return snapshot.snapshot_id if snapshot is not None else None

    def profile(self, location: str) -> list[dict]:
        result = self._conn.execute(
            """
            SELECT
                column_name,
                column_type,
                min,
                max,
                approx_count_distinct(column_name) AS distinct_count,
                count(column_name) AS non_null_count
            FROM (
                SELECT * FROM iceberg_scan(?, allow_moved_paths=true)
            )
            SUMMARIZE
            """,
            [location],
        ).fetchdf()
        return result.to_dict(orient="records")

    def close(self) -> None:
        self._conn.close()
