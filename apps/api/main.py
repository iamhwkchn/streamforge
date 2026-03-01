from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.config import settings
from api.v1.router import router as v1_router
from db.connection import connect_to_db, close_db_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await close_db_connection()

app = FastAPI(
    title=settings.APP_NAME,
    description="Metadata Catalog API for syncing MinIO to Trino",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

@app.get("/health")
def read_health():
    return {"status": "ok"}

