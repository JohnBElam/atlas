import pytest

from app.pipeline.transforms import build_pipeline_sql, sanitize_identifier, quote_column


def test_sanitize_identifier() -> None:
    assert sanitize_identifier("n1") == "n1"
    assert sanitize_identifier("1bad") == "n_1bad"


def test_quote_column() -> None:
    assert quote_column("name") == '"name"'
    assert quote_column('say"hi') == '"say""hi"'


def test_filter_values_parameterized() -> None:
    dag = {
        "nodes": [
            {"id": "n1", "type": "source", "dataset_id": "00000000-0000-0000-0000-000000000001"},
            {
                "id": "n2",
                "type": "transform",
                "transform_type": "filter",
                "config": {
                    "conditions": [
                        {"column": "status", "operator": "eq", "value": "active"},
                        {"column": "amount", "operator": "gt", "value": 100},
                    ]
                },
            },
            {
                "id": "n3",
                "type": "output",
                "config": {"namespace": "default", "table_name": "filtered", "mode": "overwrite"},
            },
        ],
        "edges": [
            {"from": "n1", "to": "n2"},
            {"from": "n2", "to": "n3"},
        ],
    }
    locations = {"00000000-0000-0000-0000-000000000001": "s3://bucket/table"}
    sql, params, _ = build_pipeline_sql(dag, locations)

    assert "?" in sql
    assert "active" not in sql
    assert "100" not in sql.split("LIMIT")[-1] if "LIMIT" in sql else "100" not in sql.replace("?", "")
    assert params == ["s3://bucket/table", "active", 100]
    assert '"status"' in sql
    assert '"amount"' in sql


def test_derive_expression_in_select() -> None:
    dag = {
        "nodes": [
            {"id": "n1", "type": "source", "dataset_id": "00000000-0000-0000-0000-000000000001"},
            {
                "id": "n2",
                "type": "transform",
                "transform_type": "derive",
                "config": {"expressions": [{"name": "total", "expr": "price * qty"}]},
            },
            {
                "id": "n3",
                "type": "output",
                "config": {"namespace": "default", "table_name": "derived", "mode": "overwrite"},
            },
        ],
        "edges": [
            {"from": "n1", "to": "n2"},
            {"from": "n2", "to": "n3"},
        ],
    }
    locations = {"00000000-0000-0000-0000-000000000001": "s3://bucket/table"}
    sql, params, _ = build_pipeline_sql(dag, locations)
    assert "(price * qty) AS \"total\"" in sql
