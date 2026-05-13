from fastapi import FastAPI

from app.core.config import settings
from app.features.system.routes import router as system_router

app = FastAPI(title=settings.app_name)
app.include_router(system_router)
