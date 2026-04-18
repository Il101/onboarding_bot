from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.ingest import router as ingest_router
from src.api.routes.knowledge import router as knowledge_router
from src.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="V-Brain API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingest_router)
app.include_router(knowledge_router)
