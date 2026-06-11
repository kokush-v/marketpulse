from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.market_data.service import UpstreamMarketDataError
from app.features.news.schemas import NewsErrorResponse, NewsSearchResponse
from app.features.news.service import NewsService, NewsServiceError

router = APIRouter(prefix="/news", tags=["news"])
current_user_dependency = Depends(get_current_user)


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=NewsErrorResponse(message=message).model_dump(),
    )


@router.get(
    "",
    response_model=NewsSearchResponse,
    responses={
        422: {"model": NewsErrorResponse, "description": "Invalid query"},
        429: {"model": NewsErrorResponse, "description": "Upstream rate limit"},
        502: {"model": NewsErrorResponse, "description": "Upstream provider failure"},
        503: {
            "model": NewsErrorResponse,
            "description": "Market data service is unavailable",
        },
        504: {"model": NewsErrorResponse, "description": "Upstream timeout"},
    },
    summary="Get latest news for a coin query",
)
async def get_coin_news(
    _: Annotated[User, current_user_dependency],
    service: Annotated[NewsService, Depends()],
    query: Annotated[str, Query(min_length=1)],
) -> NewsSearchResponse:
    try:
        return await service.search_coin_news(query)
    except (NewsServiceError, UpstreamMarketDataError) as error:
        return _error_response(error.status_code, error.message)
