#!/usr/bin/env python3
"""PyArrow → PyIceberg → MinIO → DuckDB read-back proof for S01."""

from __future__ import annotations

import sys
from pathlib import Path

import pyarrow as pa

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.catalog.iceberg_catalog import get_catalog  # noqa: E402
from app.compute.duckdb_engine import DuckDBEngine  # noqa: E402

NAMESPACE = "proof"
TABLE_NAME = "roundtrip_test"


def main() -> int:
    source = pa.table(
        {
            "id": [1, 2, 3],
            "name": ["alpha", "beta", "gamma"],
        }
    )

    engine = DuckDBEngine()
    try:
        snapshot_id = engine.write_iceberg(source, NAMESPACE, TABLE_NAME, "overwrite")
        print(f"Wrote {source.num_rows} rows (snapshot_id={snapshot_id})")

        catalog = get_catalog()
        iceberg_table = catalog.load_table(f"{NAMESPACE}.{TABLE_NAME}")
        location = iceberg_table.location()
        print(f"Iceberg table location: {location}")

        read_back = engine.read_iceberg(location)
        print(f"Read back {read_back.num_rows} rows via DuckDB iceberg_scan")

        if read_back.num_rows != source.num_rows:
            print(
                f"FAIL: row count mismatch (expected {source.num_rows}, got {read_back.num_rows})"
            )
            return 1

        print("PASS: Iceberg round-trip successful")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
