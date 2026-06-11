from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.envelope import error_envelope, success
from app.dependencies import get_db
from app.schemas.ontology import (
    LinkTypeCreate,
    LinkTypeUpdate,
    ObjectPropertyCreate,
    ObjectPropertyUpdate,
    ObjectTypeCreate,
    ObjectTypeUpdate,
)
from app.services.ontology_service import (
    OntologyNotFoundError,
    OntologyService,
    OntologyValidationError,
)

router = APIRouter(prefix="/ontology", tags=["ontology"])


def _ontology_service() -> OntologyService:
    return OntologyService()


@router.get("/types")
async def list_object_types(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    items, meta = await service.list_types(db, page=page, page_size=page_size)
    return success([item.model_dump(mode="json") for item in items], meta=meta)


@router.post("/types", status_code=201)
async def create_object_type(
    body: ObjectTypeCreate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    obj_type = await service.create_type(db, body)
    return success(obj_type.model_dump(mode="json"))


@router.get("/types/{type_id}")
async def get_object_type(
    type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        obj_type = await service.get_type(db, type_id)
        properties = await service.list_properties_for_type(db, type_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success({
        "type": obj_type.model_dump(mode="json"),
        "properties": [p.model_dump(mode="json") for p in properties],
    })


@router.put("/types/{type_id}")
async def update_object_type(
    type_id: uuid.UUID,
    body: ObjectTypeUpdate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        obj_type = await service.update_type(db, type_id, body)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except OntologyValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(obj_type.model_dump(mode="json"))


@router.delete("/types/{type_id}")
async def delete_object_type(
    type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        await service.delete_type(db, type_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.post("/types/{type_id}/properties", status_code=201)
async def create_property(
    type_id: uuid.UUID,
    body: ObjectPropertyCreate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        prop = await service.create_property(db, type_id, body)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(prop.model_dump(mode="json"))


@router.get("/properties/{property_id}")
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        prop = await service.get_property(db, property_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(prop.model_dump(mode="json"))


@router.put("/properties/{property_id}")
async def update_property(
    property_id: uuid.UUID,
    body: ObjectPropertyUpdate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        prop = await service.update_property(db, property_id, body)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(prop.model_dump(mode="json"))


@router.delete("/properties/{property_id}")
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        await service.delete_property(db, property_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.get("/links")
async def list_links(
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    links = await service.list_links(db)
    return success([link.model_dump(mode="json") for link in links])


@router.post("/links", status_code=201)
async def create_link(
    body: LinkTypeCreate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    link = await service.create_link(db, body)
    return success(link.model_dump(mode="json"))


@router.put("/links/{link_id}")
async def update_link(
    link_id: uuid.UUID,
    body: LinkTypeUpdate,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        link = await service.update_link(db, link_id, body)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(link.model_dump(mode="json"))


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        await service.delete_link(db, link_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    return success(None)


@router.get("/graph")
async def get_ontology_graph(
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    graph = await service.get_graph(db)
    return success(graph.model_dump(mode="json"))


@router.get("/types/{type_id}/objects")
async def list_objects(
    type_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        objects, meta = await service.list_objects(
            db, type_id, page=page, page_size=page_size, search=search
        )
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except OntologyValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(objects.model_dump(mode="json"), meta=meta)


@router.get("/types/{type_id}/objects/{pk}")
async def get_object(
    type_id: uuid.UUID,
    pk: str,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        obj = await service.get_object(db, type_id, pk)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except OntologyValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(obj)


@router.get("/types/{type_id}/objects/{pk}/links/{link_type_id}")
async def traverse_link(
    type_id: uuid.UUID,
    pk: str,
    link_type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: OntologyService = Depends(_ontology_service),
):
    try:
        result = await service.traverse_link(db, type_id, pk, link_type_id)
    except OntologyNotFoundError as exc:
        return error_envelope(str(exc), 404)
    except OntologyValidationError as exc:
        return error_envelope(str(exc), 400)
    return success(result.model_dump(mode="json"))
