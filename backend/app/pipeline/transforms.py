from __future__ import annotations

import re
from typing import Any

from app.pipeline.validator import DagValidationError

_IDENT_RE = re.compile(r"[^a-zA-Z0-9_]")
_DERIVE_FORBIDDEN = re.compile(r"[;]")


def sanitize_identifier(name: str) -> str:
    safe = _IDENT_RE.sub("_", name)
    if not safe or safe[0].isdigit():
        safe = f"n_{safe}"
    return safe


def quote_column(column: str) -> str:
    escaped = column.replace('"', '""')
    return f'"{escaped}"'


def validate_derive_expression(expr: str) -> None:
    if _DERIVE_FORBIDDEN.search(expr):
        raise DagValidationError("Derive expression must not contain semicolons")


class CteBuilder:
    def __init__(self) -> None:
        self._ctes: list[str] = []
        self._params: list[Any] = []

    @property
    def params(self) -> list[Any]:
        return self._params

    def add_source_cte(self, cte_name: str, location: str) -> str:
        sql = (
            f"{cte_name} AS (SELECT * FROM iceberg_scan(?, allow_moved_paths=true))"
        )
        self._ctes.append(sql)
        self._params.append(location)
        return cte_name

    def add_transform_cte(
        self,
        cte_name: str,
        input_cte: str,
        transform_type: str,
        config: dict[str, Any],
    ) -> str:
        if transform_type == "filter":
            sql = self._build_filter(cte_name, input_cte, config)
        elif transform_type == "select":
            sql = self._build_select(cte_name, input_cte, config)
        elif transform_type == "rename":
            sql = self._build_rename(cte_name, input_cte, config)
        elif transform_type == "cast":
            sql = self._build_cast(cte_name, input_cte, config)
        elif transform_type == "derive":
            sql = self._build_derive(cte_name, input_cte, config)
        elif transform_type == "sort":
            sql = self._build_sort(cte_name, input_cte, config)
        elif transform_type == "limit":
            sql = self._build_limit(cte_name, input_cte, config)
        elif transform_type == "deduplicate":
            sql = self._build_deduplicate(cte_name, input_cte, config)
        else:
            raise DagValidationError(f"Unsupported transform type: {transform_type}")

        self._ctes.append(sql)
        return cte_name

    def build_final_query(self, final_cte: str) -> str:
        with_clause = "WITH " + ", ".join(self._ctes)
        return f"{with_clause} SELECT * FROM {final_cte}"

    def _build_filter(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        conditions = config.get("conditions", [])
        if not conditions:
            return f"{cte_name} AS (SELECT * FROM {input_cte})"

        clauses: list[str] = []
        for cond in conditions:
            column = quote_column(cond["column"])
            operator = cond["operator"]
            value = cond.get("value")

            if operator == "eq":
                clauses.append(f"{column} = ?")
                self._params.append(value)
            elif operator == "neq":
                clauses.append(f"{column} <> ?")
                self._params.append(value)
            elif operator == "gt":
                clauses.append(f"{column} > ?")
                self._params.append(value)
            elif operator == "gte":
                clauses.append(f"{column} >= ?")
                self._params.append(value)
            elif operator == "lt":
                clauses.append(f"{column} < ?")
                self._params.append(value)
            elif operator == "lte":
                clauses.append(f"{column} <= ?")
                self._params.append(value)
            elif operator == "in":
                values = value if isinstance(value, list) else [value]
                placeholders = ", ".join("?" for _ in values)
                clauses.append(f"{column} IN ({placeholders})")
                self._params.extend(values)
            elif operator == "not_in":
                values = value if isinstance(value, list) else [value]
                placeholders = ", ".join("?" for _ in values)
                clauses.append(f"{column} NOT IN ({placeholders})")
                self._params.extend(values)
            elif operator == "is_null":
                clauses.append(f"{column} IS NULL")
            elif operator == "is_not_null":
                clauses.append(f"{column} IS NOT NULL")
            else:
                raise DagValidationError(f"Unknown filter operator: {operator}")

        where_clause = " AND ".join(clauses)
        return f"{cte_name} AS (SELECT * FROM {input_cte} WHERE {where_clause})"

    def _build_select(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        columns = config.get("columns", [])
        if not columns:
            raise DagValidationError("Select transform requires columns")
        cols = ", ".join(quote_column(c) for c in columns)
        return f"{cte_name} AS (SELECT {cols} FROM {input_cte})"

    def _build_rename(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        mapping = config.get("mapping", {})
        if not mapping:
            return f"{cte_name} AS (SELECT * FROM {input_cte})"
        parts = [f"{quote_column(old)} AS {quote_column(new)}" for old, new in mapping.items()]
        return f"{cte_name} AS (SELECT {', '.join(parts)} FROM {input_cte})"

    def _build_cast(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        columns = config.get("columns", [])
        type_map = {
            "string": "VARCHAR",
            "integer": "BIGINT",
            "float": "DOUBLE",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMP",
        }
        casts = []
        for col_def in columns:
            col = quote_column(col_def["column"])
            to_type = type_map.get(col_def["to_type"])
            if not to_type:
                raise DagValidationError(f"Unknown cast type: {col_def['to_type']}")
            casts.append(f"CAST({col} AS {to_type}) AS {col}")
        return f"{cte_name} AS (SELECT {', '.join(casts)} FROM {input_cte})"

    def _build_derive(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        expressions = config.get("expressions", [])
        parts = ["*"]
        for expr_def in expressions:
            validate_derive_expression(expr_def["expr"])
            name = quote_column(expr_def["name"])
            parts.append(f"({expr_def['expr']}) AS {name}")
        select_clause = ", ".join(parts)
        return f"{cte_name} AS (SELECT {select_clause} FROM {input_cte})"

    def _build_sort(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        columns = config.get("columns", [])
        if not columns:
            return f"{cte_name} AS (SELECT * FROM {input_cte})"
        order_parts = []
        for col_def in columns:
            direction = "DESC" if col_def.get("direction", "asc").lower() == "desc" else "ASC"
            order_parts.append(f"{quote_column(col_def['column'])} {direction}")
        return f"{cte_name} AS (SELECT * FROM {input_cte} ORDER BY {', '.join(order_parts)})"

    def _build_limit(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        n = config.get("n", 100)
        return f"{cte_name} AS (SELECT * FROM {input_cte} LIMIT {int(n)})"

    def _build_deduplicate(self, cte_name: str, input_cte: str, config: dict[str, Any]) -> str:
        subset = config.get("subset")
        if subset:
            cols = ", ".join(quote_column(c) for c in subset)
            return (
                f"{cte_name} AS (SELECT DISTINCT ON ({cols}) * FROM {input_cte})"
            )
        return f"{cte_name} AS (SELECT DISTINCT * FROM {input_cte})"


def build_pipeline_sql(
    dag_json: dict[str, Any],
    dataset_locations: dict[str, str],
) -> tuple[str, list[Any], dict[str, Any]]:
    from app.pipeline.validator import topological_sort

    sorted_nodes = topological_sort(dag_json)
    edges = dag_json["edges"]

    incoming: dict[str, str] = {}
    for edge in edges:
        incoming[edge["to"]] = edge["from"]

    builder = CteBuilder()
    cte_names: dict[str, str] = {}
    output_config: dict[str, Any] = {}

    for node in sorted_nodes:
        node_id = node["id"]
        cte_name = sanitize_identifier(node_id)
        cte_names[node_id] = cte_name
        node_type = node["type"]

        if node_type == "source":
            dataset_id = str(node["dataset_id"])
            location = dataset_locations.get(dataset_id)
            if not location:
                raise DagValidationError(f"Dataset not found for source node: {dataset_id}")
            builder.add_source_cte(cte_name, location)
        elif node_type == "transform":
            parent_id = incoming[node_id]
            parent_cte = cte_names[parent_id]
            builder.add_transform_cte(
                cte_name,
                parent_cte,
                node["transform_type"],
                node.get("config", {}),
            )
        elif node_type == "output":
            parent_id = incoming[node_id]
            cte_names[node_id] = cte_names[parent_id]
            output_config = node.get("config", {})

    final_cte = cte_names[sorted_nodes[-1]["id"]]
    if sorted_nodes[-1]["type"] != "output":
        raise DagValidationError("Last node in topological order must be output")

    parent_of_output = incoming[sorted_nodes[-1]["id"]]
    final_cte = cte_names[parent_of_output]
    sql = builder.build_final_query(final_cte)
    return sql, builder.params, output_config
