from __future__ import annotations

from typing import Protocol

import pyarrow as pa


class ComputeEngine(Protocol):
    def query(self, sql: str) -> pa.Table: ...

    def read_iceberg(self, location: str) -> pa.Table: ...

    def write_iceberg(
        self,
        table: pa.Table,
        namespace: str,
        table_name: str,
        mode: str,
    ) -> int | None: ...

    def profile(self, location: str) -> list[dict]: ...
