from fastapi import APIRouter
from .metadata.router import router as metadata_router
from .query.router import router as query_router

router = APIRouter()

router.include_router(metadata_router, prefix="/metadata", tags=["Metadata"])
router.include_router(query_router, prefix="/query", tags=["Query"])
