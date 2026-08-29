from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.features.ai_assistant.routes import router as assistant_router
from app.features.alerts.routes import router as alerts_router
from app.features.auth.routes import router as auth_router
from app.features.market_data.routes import router as market_data_router
from app.features.news.routes import router as news_router
from app.features.notifications.routes import router as notifications_router
from app.features.system.routes import router as system_router
from app.features.telegram.routes import router as telegram_router
from app.features.telegram.service import get_telegram_bot_app
from app.features.watchlists.routes import router as watchlists_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.telegram_bot = get_telegram_bot_app()
    await app.state.telegram_bot.initialize()
    try:
        yield
    finally:
        await app.state.telegram_bot.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(system_router)
app.include_router(assistant_router)
app.include_router(market_data_router)
app.include_router(news_router)
app.include_router(auth_router)
app.include_router(watchlists_router)
app.include_router(alerts_router)
app.include_router(telegram_router)
app.include_router(notifications_router)
