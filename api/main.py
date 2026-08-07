from fastapi import FastAPI

from api.config import settings
from api.routes.dashboard import router as dashboard_router
from api.routes.health import router as health_router
from api.routes.screening import router as screening_router

app = FastAPI(title=settings.app_name, version=settings.api_version)
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(screening_router)
