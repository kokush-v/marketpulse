from fastapi import FastAPI, HTTPException

from app.api.health import router as health_router
from app.api.market_data import router as market_data_router
from app.core.config import get_settings
from app.core.exception_handlers import http_exception_handler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.include_router(health_router)
    app.include_router(market_data_router)
    return app


app = create_app()
