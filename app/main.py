from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.as_set import router as as_set_router
from app.api.v1.autonomous_system import router as autonomous_system_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.route_set import router as route_set_router
from app.config import settings

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
)

app.include_router(health_router)
app.include_router(as_set_router)
app.include_router(autonomous_system_router)
app.include_router(jobs_router)
app.include_router(route_set_router)
