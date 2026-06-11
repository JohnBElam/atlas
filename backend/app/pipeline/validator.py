from __future__ import annotations

from typing import Any

PHASE1_TRANSFORM_TYPES = {
    "filter",
    "select",
    "rename",
    "cast",
    "derive",
    "sort",
    "limit",
    "deduplicate",
}

NODE_TYPES = {"source", "transform", "output"}


class DagValidationError(Exception):
    pass


def validate_dag(dag_json: dict[str, Any]) -> None:
    nodes = dag_json.get("nodes", [])
    edges = dag_json.get("edges", [])

    if not nodes:
        raise DagValidationError("DAG must contain at least one node")

    node_ids = {node["id"] for node in nodes}
    for edge in edges:
        if edge["from"] not in node_ids:
            raise DagValidationError(f"Unknown source node in edge: {edge['from']}")
        if edge["to"] not in node_ids:
            raise DagValidationError(f"Unknown target node in edge: {edge['to']}")

    outputs = [n for n in nodes if n.get("type") == "output"]
    if len(outputs) != 1:
        raise DagValidationError("DAG must contain exactly one output node")

    sources = [n for n in nodes if n.get("type") == "source"]
    if not sources:
        raise DagValidationError("DAG must contain at least one source node")

    for node in nodes:
        node_type = node.get("type")
        if node_type not in NODE_TYPES:
            raise DagValidationError(f"Unknown node type: {node_type}")
        if node_type == "source" and not node.get("dataset_id"):
            raise DagValidationError(f"Source node {node['id']} missing dataset_id")
        if node_type == "transform":
            transform_type = node.get("transform_type")
            if transform_type not in PHASE1_TRANSFORM_TYPES:
                raise DagValidationError(f"Unknown or unsupported transform type: {transform_type}")
        if node_type == "output":
            config = node.get("config", {})
            if not config.get("table_name"):
                raise DagValidationError(f"Output node {node['id']} missing table_name")

    adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}
    reverse_adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        reverse_adjacency[edge["to"]].append(edge["from"])

    if _has_cycle(node_ids, adjacency):
        raise DagValidationError("DAG contains a cycle")

    output_id = outputs[0]["id"]
    reachable_from_sources: set[str] = set()
    for source in sources:
        reachable_from_sources |= _reachable(source["id"], adjacency)

    all_node_ids = set(node_ids)
    if reachable_from_sources != all_node_ids:
        unreachable = all_node_ids - reachable_from_sources
        raise DagValidationError(f"Nodes not reachable from sources: {unreachable}")

    reachable_to_output = _reachable_reverse(output_id, reverse_adjacency)
    if reachable_to_output != all_node_ids:
        unreachable = all_node_ids - reachable_to_output
        raise DagValidationError(f"Nodes cannot reach output: {unreachable}")


def _has_cycle(node_ids: set[str], adjacency: dict[str, list[str]]) -> bool:
    visited: set[str] = set()
    stack: set[str] = set()

    def visit(node: str) -> bool:
        visited.add(node)
        stack.add(node)
        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                if visit(neighbor):
                    return True
            elif neighbor in stack:
                return True
        stack.remove(node)
        return False

    for node in node_ids:
        if node not in visited and visit(node):
            return True
    return False


def _reachable(start: str, adjacency: dict[str, list[str]]) -> set[str]:
    result: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(adjacency.get(current, []))
    return result


def _reachable_reverse(end: str, reverse_adjacency: dict[str, list[str]]) -> set[str]:
    result: set[str] = set()
    stack = [end]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(reverse_adjacency.get(current, []))
    return result


def topological_sort(dag_json: dict[str, Any]) -> list[dict[str, Any]]:
    validate_dag(dag_json)
    nodes = dag_json["nodes"]
    edges = dag_json["edges"]
    node_map = {n["id"]: n for n in nodes}

    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    adjacency: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    sorted_ids: list[str] = []
    while queue:
        current = queue.pop(0)
        sorted_ids.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return [node_map[nid] for nid in sorted_ids]
