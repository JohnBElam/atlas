#!/usr/bin/env python3
"""Seed a connected ontology demo from existing customers/products/orders datasets.

Requires the API server and ingested demo datasets (customers, products, orders).
Run: python backend/scripts/seed_ontology_demo.py
"""

from __future__ import annotations

import os
import sys

import httpx

API_URL = os.environ.get("ATLAS_API_URL", "http://127.0.0.1:8000/api/v1")


def api(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    response = client.request(method, f"{API_URL}{path}", **kwargs)
    body = response.json()
    if response.status_code >= 400 or body.get("error"):
        raise RuntimeError(f"{method} {path} failed ({response.status_code}): {body.get('error')}")
    return body["data"]


def find_dataset(client: httpx.Client, table_name: str) -> dict:
    data = api(client, "GET", "/datasets", params={"page": 1, "page_size": 100})
    for ds in data:
        if ds["name"] == table_name:
            return ds
    raise RuntimeError(
        f"Dataset '{table_name}' not found. Ingest customers, products, and orders first."
    )


def find_type(client: httpx.Client, name: str) -> dict | None:
    data = api(client, "GET", "/ontology/types", params={"page": 1, "page_size": 100})
    return next((t for t in data if t["name"] == name), None)


def get_type_detail(client: httpx.Client, type_id: str) -> dict:
    return api(client, "GET", f"/ontology/types/{type_id}")


def ensure_property(
    client: httpx.Client,
    type_id: str,
    existing: list[dict],
    *,
    name: str,
    display_name: str,
    dataset_id: str,
    column_name: str,
    sort_order: int,
) -> dict:
    match = next((p for p in existing if p["name"] == name), None)
    if match:
        if match.get("dataset_id") != dataset_id or match.get("column_name") != column_name:
            api(
                client,
                "PUT",
                f"/ontology/properties/{match['id']}",
                json={"dataset_id": dataset_id, "column_name": column_name},
            )
        return match

    return api(
        client,
        "POST",
        f"/ontology/types/{type_id}/properties",
        json={
            "name": name,
            "display_name": display_name,
            "data_type": "string",
            "dataset_id": dataset_id,
            "column_name": column_name,
            "sort_order": sort_order,
        },
    )


def ensure_type(
    client: httpx.Client,
    *,
    name: str,
    display_name: str,
    description: str,
    color: str,
) -> dict:
    existing = find_type(client, name)
    if existing:
        return existing
    return api(
        client,
        "POST",
        "/ontology/types",
        json={
            "name": name,
            "display_name": display_name,
            "description": description,
            "color": color,
        },
    )


def set_primary_key(client: httpx.Client, type_id: str, property_id: str) -> None:
    api(
        client,
        "PUT",
        f"/ontology/types/{type_id}",
        json={"primary_key_property_id": property_id},
    )


def remove_wrong_dataset_properties(
    client: httpx.Client,
    type_id: str,
    properties: list[dict],
    allowed_dataset_id: str,
) -> list[dict]:
    kept: list[dict] = []
    for prop in properties:
        if prop.get("dataset_id") and prop["dataset_id"] != allowed_dataset_id:
            api(client, "DELETE", f"/ontology/properties/{prop['id']}")
        else:
            kept.append(prop)
    return kept


def ensure_link(
    client: httpx.Client,
    existing_links: list[dict],
    *,
    name: str,
    display_name: str,
    from_type_id: str,
    to_type_id: str,
    from_property_id: str,
    to_property_id: str,
    cardinality: str,
) -> dict:
    match = next((link for link in existing_links if link["name"] == name), None)
    if match:
        return match
    return api(
        client,
        "POST",
        "/ontology/links",
        json={
            "name": name,
            "display_name": display_name,
            "from_object_type_id": from_type_id,
            "to_object_type_id": to_type_id,
            "from_property_id": from_property_id,
            "to_property_id": to_property_id,
            "cardinality": cardinality,
        },
    )


def prop_id(properties: list[dict], name: str) -> str:
    match = next(p for p in properties if p["name"] == name)
    return match["id"]


def main() -> int:
    with httpx.Client(timeout=30.0) as client:
        customers_ds = find_dataset(client, "customers")
        products_ds = find_dataset(client, "products")
        orders_ds = find_dataset(client, "orders")

        customer_type = ensure_type(
            client,
            name="customer",
            display_name="Customer",
            description="Retail customers",
            color="#6366f1",
        )
        product_type = ensure_type(
            client,
            name="product",
            display_name="Product",
            description="Catalog products",
            color="#22c55e",
        )
        order_type = ensure_type(
            client,
            name="order",
            display_name="Order",
            description="Customer orders",
            color="#f97316",
        )

        customer_detail = get_type_detail(client, customer_type["id"])
        customer_props = remove_wrong_dataset_properties(
            client,
            customer_type["id"],
            customer_detail["properties"],
            customers_ds["id"],
        )
        customer_props = [
            ensure_property(
                client,
                customer_type["id"],
                customer_props,
                name="customer_id",
                display_name="Customer ID",
                dataset_id=customers_ds["id"],
                column_name="customer_id",
                sort_order=0,
            ),
            ensure_property(
                client,
                customer_type["id"],
                customer_props,
                name="name",
                display_name="Name",
                dataset_id=customers_ds["id"],
                column_name="name",
                sort_order=1,
            ),
            ensure_property(
                client,
                customer_type["id"],
                customer_props,
                name="email",
                display_name="Email",
                dataset_id=customers_ds["id"],
                column_name="email",
                sort_order=2,
            ),
            ensure_property(
                client,
                customer_type["id"],
                customer_props,
                name="city",
                display_name="City",
                dataset_id=customers_ds["id"],
                column_name="city",
                sort_order=3,
            ),
            ensure_property(
                client,
                customer_type["id"],
                customer_props,
                name="segment",
                display_name="Segment",
                dataset_id=customers_ds["id"],
                column_name="segment",
                sort_order=4,
            ),
        ]
        set_primary_key(client, customer_type["id"], prop_id(customer_props, "customer_id"))

        product_detail = get_type_detail(client, product_type["id"])
        product_props = product_detail["properties"]
        product_props = [
            ensure_property(
                client,
                product_type["id"],
                product_props,
                name="product_id",
                display_name="Product ID",
                dataset_id=products_ds["id"],
                column_name="product_id",
                sort_order=0,
            ),
            ensure_property(
                client,
                product_type["id"],
                product_props,
                name="name",
                display_name="Name",
                dataset_id=products_ds["id"],
                column_name="name",
                sort_order=1,
            ),
            ensure_property(
                client,
                product_type["id"],
                product_props,
                name="category",
                display_name="Category",
                dataset_id=products_ds["id"],
                column_name="category",
                sort_order=2,
            ),
            ensure_property(
                client,
                product_type["id"],
                product_props,
                name="unit_price",
                display_name="Unit Price",
                dataset_id=products_ds["id"],
                column_name="unit_price",
                sort_order=3,
            ),
        ]
        set_primary_key(client, product_type["id"], prop_id(product_props, "product_id"))

        order_detail = get_type_detail(client, order_type["id"])
        order_props = order_detail["properties"]
        order_props = [
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="order_id",
                display_name="Order ID",
                dataset_id=orders_ds["id"],
                column_name="order_id",
                sort_order=0,
            ),
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="customer_id",
                display_name="Customer ID",
                dataset_id=orders_ds["id"],
                column_name="customer_id",
                sort_order=1,
            ),
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="product_id",
                display_name="Product ID",
                dataset_id=orders_ds["id"],
                column_name="product_id",
                sort_order=2,
            ),
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="order_date",
                display_name="Order Date",
                dataset_id=orders_ds["id"],
                column_name="order_date",
                sort_order=3,
            ),
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="status",
                display_name="Status",
                dataset_id=orders_ds["id"],
                column_name="status",
                sort_order=4,
            ),
            ensure_property(
                client,
                order_type["id"],
                order_props,
                name="amount",
                display_name="Amount",
                dataset_id=orders_ds["id"],
                column_name="amount",
                sort_order=5,
            ),
        ]
        set_primary_key(client, order_type["id"], prop_id(order_props, "order_id"))

        customer_detail = get_type_detail(client, customer_type["id"])
        product_detail = get_type_detail(client, product_type["id"])
        order_detail = get_type_detail(client, order_type["id"])
        customer_props = customer_detail["properties"]
        product_props = product_detail["properties"]
        order_props = order_detail["properties"]

        links = api(client, "GET", "/ontology/links")
        ensure_link(
            client,
            links,
            name="customer_orders",
            display_name="placed orders",
            from_type_id=customer_type["id"],
            to_type_id=order_type["id"],
            from_property_id=prop_id(customer_props, "customer_id"),
            to_property_id=prop_id(order_props, "customer_id"),
            cardinality="one-to-many",
        )
        ensure_link(
            client,
            links,
            name="product_orders",
            display_name="ordered in",
            from_type_id=product_type["id"],
            to_type_id=order_type["id"],
            from_property_id=prop_id(product_props, "product_id"),
            to_property_id=prop_id(order_props, "product_id"),
            cardinality="one-to-many",
        )

        objects = api(
            client,
            "GET",
            f"/ontology/types/{customer_type['id']}/objects",
            params={"page": 1, "page_size": 5},
        )
        graph = api(client, "GET", "/ontology/graph")

        print("Ontology demo seeded successfully.")
        print(f"  Object types: customer, product, order")
        print(f"  Links: {len(graph['edges'])} edge(s) in graph")
        print(f"  Customer browser rows (sample): {len(objects['rows'])}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
