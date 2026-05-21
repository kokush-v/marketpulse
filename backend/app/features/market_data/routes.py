from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.features.market_data.schemas import MarketOverviewErrorResponse, MarketOverviewResponse
from app.features.market_data.service import MarketDataService, UpstreamMarketDataError

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get(
    "/overview",
    response_model=MarketOverviewResponse,
    responses={
        429: {"model": MarketOverviewErrorResponse, "description": "Upstream rate limit"},
        502: {"model": MarketOverviewErrorResponse, "description": "Upstream provider failure"},
        503: {
            "model": MarketOverviewErrorResponse,
            "description": "Market data service is unavailable",
        },
        504: {"model": MarketOverviewErrorResponse, "description": "Upstream timeout"},
    },
    summary="Get public crypto market overview",
)
async def get_market_overview(
    service: Annotated[MarketDataService, Depends()],
) -> MarketOverviewResponse:
    try:
        return await service.get_market_overview()
    except UpstreamMarketDataError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"message": error.message},
        )
