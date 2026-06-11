import pytest

from app.pipeline.validator import DagValidationError, validate_dag


def _valid_dag() -> dict:
    return {
        "nodes": [
            {"id": "n1", "type": "source", "dataset_id": "00000000-0000-0000-0000-000000000001"},
            {
                "id": "n2",
                "type": "transform",
                "transform_type": "filter",
                "config": {
                    "conditions": [{"column": "status", "operator": "eq", "value": "active"}]
                },
            },
            {
                "id": "n3",
                "type": "output",
                "config": {"namespace": "default", "table_name": "active_orders", "mode": "overwrite"},
            },
        ],
        "edges": [
            {"from": "n1", "to": "n2"},
            {"from": "n2", "to": "n3"},
        ],
    }


def test_valid_dag_passes() -> None:
    validate_dag(_valid_dag())


def test_cycle_rejected() -> None:
    dag = _valid_dag()
    dag["edges"].append({"from": "n3", "to": "n1"})
    with pytest.raises(DagValidationError, match="cycle"):
        validate_dag(dag)


def test_multiple_outputs_rejected() -> None:
    dag = _valid_dag()
    dag["nodes"].append(
        {"id": "n4", "type": "output", "config": {"table_name": "other", "mode": "overwrite"}}
    )
    with pytest.raises(DagValidationError, match="exactly one output"):
        validate_dag(dag)


def test_unreachable_node_rejected() -> None:
    dag = _valid_dag()
    dag["nodes"].append({"id": "orphan", "type": "source", "dataset_id": "00000000-0000-0000-0000-000000000002"})
    with pytest.raises(DagValidationError, match="reach"):
        validate_dag(dag)


def test_unknown_transform_rejected() -> None:
    dag = _valid_dag()
    dag["nodes"][1]["transform_type"] = "join"
    with pytest.raises(DagValidationError, match="Unknown or unsupported"):
        validate_dag(dag)
