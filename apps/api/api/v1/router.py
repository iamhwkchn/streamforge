from fastapi import APIRouter
from .metadata.router import router as metadata_router

router = APIRouter()

router.include_router(metadata_router, prefix="/metadata", tags=["Metadata"])
