from fastapi import APIRouter

from app.api.envelope import success
from app.api.v1.sources import router as sources_router

router = APIRouter()

router.include_router(sources_router)


@router.get("/health")
async def health() -> dict:
    return success({"status": "ok"})
