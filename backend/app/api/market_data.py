from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.deps.auth import require_authenticated_user
from app.market_data.errors import MarketDataError
from app.market_data.schemas import (
    ErrorResponse,
    HistoryRange,
    HistoryResolution,
    HistoryResponse,
    QuoteResponse,
    SymbolSearchResponse,
)
from app.market_data.service import MarketDataService, get_market_data_service

router = APIRouter(
    prefix="/api/market-data",
    tags=["market-data"],
    dependencies=[Depends(require_authenticated_user)],
)

MarketDataServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]

ERROR_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


@router.get(
    "/symbols/search",
    response_model=SymbolSearchResponse,
    operation_id="searchMarketDataSymbols",
    responses=ERROR_RESPONSES,
)
def search_market_data_symbols(
    service: MarketDataServiceDep,
    query: Annotated[str, Query(min_length=1, max_length=32)],
) -> SymbolSearchResponse | JSONResponse:
    try:
        return service.search_symbols(query)
    except MarketDataError as exc:
        return market_data_error_response(exc)


@router.get(
    "/symbols/{symbol}/quote",
    response_model=QuoteResponse,
    operation_id="getMarketDataQuote",
    responses=ERROR_RESPONSES,
)
def get_market_data_quote(
    service: MarketDataServiceDep,
    symbol: str,
) -> QuoteResponse | JSONResponse:
    try:
        return service.get_quote(symbol)
    except MarketDataError as exc:
        return market_data_error_response(exc)


@router.get(
    "/symbols/{symbol}/history",
    response_model=HistoryResponse,
    operation_id="getMarketDataHistory",
    responses=ERROR_RESPONSES,
)
def get_market_data_history(
    service: MarketDataServiceDep,
    symbol: str,
    history_range: Annotated[HistoryRange, Query(alias="range")] = HistoryRange.ONE_MONTH,
    resolution: HistoryResolution = HistoryResolution.DAILY,
) -> HistoryResponse | JSONResponse:
    try:
        return service.get_daily_history(symbol, history_range, resolution)
    except MarketDataError as exc:
        return market_data_error_response(exc)


def market_data_error_response(exc: MarketDataError) -> JSONResponse:
    payload = ErrorResponse(code=exc.code.value, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())
