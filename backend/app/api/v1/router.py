from fastapi import APIRouter

from app.api.envelope import success
from app.api.v1.datasets import router as datasets_router
from app.api.v1.lineage import router as lineage_router
from app.api.v1.ontology import router as ontology_router
from app.api.v1.pipelines import router as pipelines_router
from app.api.v1.sources import router as sources_router

router = APIRouter()

router.include_router(sources_router)
router.include_router(datasets_router)
router.include_router(pipelines_router)
router.include_router(lineage_router)
router.include_router(ontology_router)


@router.get("/health")
async def health() -> dict:
    return success({"status": "ok"})
