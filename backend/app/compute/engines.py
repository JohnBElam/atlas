from __future__ import annotations

from app.compute.duckdb_engine import DuckDBEngine
from app.compute.spark_engine import SparkEngine

ENGINES: dict[str, type] = {
    "duckdb": DuckDBEngine,
    "spark": SparkEngine,
}

DEFAULT_ENGINE = "duckdb"
