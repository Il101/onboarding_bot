from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.admin import AdminAuthMiddleware, router as admin_router
from src.api.routes.ingest import router as ingest_router
from src.api.routes.knowledge import router as knowledge_router
from src.core.logging import setup_logging


from fastapi.responses import RedirectResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="V-Brain API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AdminAuthMiddleware)
app.include_router(ingest_router)
app.include_router(knowledge_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/admin")


@app.get("/admin")
async def admin_redirect():
    return RedirectResponse(url="/api/admin/")
