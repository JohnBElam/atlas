from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PropertyDataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"


class LinkCardinality(str, Enum):
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_MANY = "many-to-many"


class ObjectTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    icon: str = "box"
    color: str = "#6366f1"


class ObjectTypeUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    primary_key_property_id: UUID | None = None


class ObjectTypeResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    icon: str
    color: str
    primary_key_property_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ObjectPropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    data_type: PropertyDataType
    is_required: bool = False
    dataset_id: UUID | None = None
    column_name: str | None = None
    description: str | None = None
    sort_order: int = 0


class ObjectPropertyUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    data_type: PropertyDataType | None = None
    is_required: bool | None = None
    dataset_id: UUID | None = None
    column_name: str | None = None
    description: str | None = None
    sort_order: int | None = None


class ObjectPropertyResponse(BaseModel):
    id: UUID
    object_type_id: UUID
    name: str
    display_name: str
    data_type: str
    is_required: bool
    dataset_id: UUID | None = None
    column_name: str | None = None
    description: str | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LinkTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    from_object_type_id: UUID
    to_object_type_id: UUID
    cardinality: LinkCardinality
    from_property_id: UUID
    to_property_id: UUID
    description: str | None = None


class LinkTypeUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class LinkTypeResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    from_object_type_id: UUID
    to_object_type_id: UUID
    cardinality: str
    from_property_id: UUID
    to_property_id: UUID
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OntologyGraphNode(BaseModel):
    id: str
    type: str = "default"
    position: dict[str, float]
    data: dict[str, Any]


class OntologyGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class OntologyGraphResponse(BaseModel):
    nodes: list[OntologyGraphNode]
    edges: list[OntologyGraphEdge]


class ObjectListResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
