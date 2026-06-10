from __future__ import annotations

import pyarrow as pa

_SPARK_STUB_MSG = "SparkEngine is not implemented in Phase 1; use DuckDBEngine instead."


class SparkEngine:
    def query(self, sql: str) -> pa.Table:
        raise NotImplementedError(_SPARK_STUB_MSG)

    def read_iceberg(self, location: str) -> pa.Table:
        raise NotImplementedError(_SPARK_STUB_MSG)

    def write_iceberg(
        self,
        table: pa.Table,
        namespace: str,
        table_name: str,
        mode: str,
    ) -> int | None:
        raise NotImplementedError(_SPARK_STUB_MSG)

    def profile(self, location: str) -> list[dict]:
        raise NotImplementedError(_SPARK_STUB_MSG)
