from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.features.auth.routes import router as auth_router
from app.features.market_data.routes import router as market_data_router
from app.features.system.routes import router as system_router
from app.features.watchlists.routes import router as watchlists_router

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(system_router)
app.include_router(market_data_router)
app.include_router(auth_router)
app.include_router(watchlists_router)
