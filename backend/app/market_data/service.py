from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import status

from app.core.config import get_settings
from app.market_data.errors import MarketDataError, MarketDataErrorCode
from app.market_data.provider import FinnhubProvider, JsonObject
from app.market_data.schemas import (
    HistoryPoint,
    HistoryRange,
    HistoryResolution,
    HistoryResponse,
    QuoteResponse,
    SymbolSearchResponse,
    SymbolSearchResult,
    unix_seconds_to_datetime,
)


class MarketDataService:
    def __init__(self, provider: FinnhubProvider) -> None:
        self._provider = provider

    def search_symbols(self, query: str) -> SymbolSearchResponse:
        normalized_query = normalize_requested_symbol(query)
        payload = self._provider.search_symbols(normalized_query)
        results = payload.get("result")
        if not isinstance(results, list):
            raise malformed_provider_response_error()

        return SymbolSearchResponse(
            query=normalized_query,
            results=[self._map_symbol_result(item) for item in results if isinstance(item, dict)],
        )

    def get_quote(self, symbol: str) -> QuoteResponse:
        normalized_symbol = normalize_requested_symbol(symbol)
        payload = self._provider.get_quote(normalized_symbol)
        current_price = read_number(payload, "c")

        if current_price is None:
            raise malformed_provider_response_error()

        if current_price <= 0:
            raise MarketDataError(
                code=MarketDataErrorCode.SYMBOL_NOT_FOUND,
                message="Latest quote data is unavailable for this symbol.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return QuoteResponse(
            symbol=normalized_symbol,
            current_price=current_price,
            daily_change=read_number(payload, "d"),
            daily_percent_change=read_number(payload, "dp"),
            open_price=read_non_negative_number(payload, "o"),
            high_price=read_non_negative_number(payload, "h"),
            low_price=read_non_negative_number(payload, "l"),
            previous_close=read_non_negative_number(payload, "pc"),
            quote_timestamp=unix_seconds_to_datetime(read_number(payload, "t")),
        )

    def get_daily_history(
        self,
        symbol: str,
        history_range: HistoryRange,
        resolution: HistoryResolution,
    ) -> HistoryResponse:
        if resolution != HistoryResolution.DAILY:
            raise MarketDataError(
                code=MarketDataErrorCode.CHART_UNAVAILABLE,
                message="Only daily historical chart data is supported.",
                status_code=422,
            )

        normalized_symbol = normalize_requested_symbol(symbol)
        to_timestamp = int(datetime.now(tz=UTC).timestamp())
        from_timestamp = int((datetime.now(tz=UTC) - range_to_timedelta(history_range)).timestamp())
        payload = self._provider.get_daily_candles(normalized_symbol, from_timestamp, to_timestamp)

        provider_status = payload.get("s")
        if provider_status != "ok":
            raise MarketDataError(
                code=MarketDataErrorCode.CHART_UNAVAILABLE,
                message="Historical chart data is unavailable for this request.",
            )

        points = self._map_history_points(payload)
        if not points:
            raise MarketDataError(
                code=MarketDataErrorCode.CHART_UNAVAILABLE,
                message="Historical chart data is unavailable for this request.",
            )

        return HistoryResponse(
            symbol=normalized_symbol,
            range=history_range,
            resolution=HistoryResolution.DAILY,
            points=points,
        )

    def _map_symbol_result(self, item: dict[str, Any]) -> SymbolSearchResult:
        symbol = item.get("symbol")
        display_symbol = item.get("displaySymbol")
        return SymbolSearchResult(
            symbol=normalize_symbol(str(symbol or display_symbol or "")),
            display_symbol=str(display_symbol) if display_symbol else None,
            description=str(item["description"]) if item.get("description") else None,
            type=str(item["type"]) if item.get("type") else None,
        )

    def _map_history_points(self, payload: JsonObject) -> list[HistoryPoint]:
        timestamps = payload.get("t")
        opens = payload.get("o")
        highs = payload.get("h")
        lows = payload.get("l")
        closes = payload.get("c")
        volumes = payload.get("v")

        series = [timestamps, opens, highs, lows, closes, volumes]
        if not all(isinstance(values, list) for values in series):
            raise malformed_provider_response_error()

        if len({len(values) for values in series}) != 1:
            raise malformed_provider_response_error()

        points: list[HistoryPoint] = []
        for index, _timestamp in enumerate(timestamps):
            point_timestamp = unix_seconds_to_datetime(read_list_number(timestamps, index))
            open_price = read_list_number(opens, index)
            high_price = read_list_number(highs, index)
            low_price = read_list_number(lows, index)
            close_price = read_list_number(closes, index)
            volume = read_list_number(volumes, index)

            if None in {point_timestamp, open_price, high_price, low_price, close_price, volume}:
                raise malformed_provider_response_error()

            points.append(
                HistoryPoint(
                    timestamp=point_timestamp,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                )
            )

        return points


def get_market_data_service() -> MarketDataService:
    return MarketDataService(FinnhubProvider(get_settings()))


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def normalize_requested_symbol(symbol: str) -> str:
    normalized_symbol = normalize_symbol(symbol)
    if not normalized_symbol:
        raise MarketDataError(
            code=MarketDataErrorCode.INVALID_SYMBOL,
            message="Ticker symbol is required.",
            status_code=422,
        )
    return normalized_symbol


def range_to_timedelta(history_range: HistoryRange) -> timedelta:
    if history_range == HistoryRange.ONE_MONTH:
        return timedelta(days=31)
    if history_range == HistoryRange.THREE_MONTHS:
        return timedelta(days=93)
    return timedelta(days=366)


def read_number(payload: JsonObject, key: str) -> float | None:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def read_non_negative_number(payload: JsonObject, key: str) -> float | None:
    value = read_number(payload, key)
    if value is None or value < 0:
        return None
    return value


def read_list_number(values: list[Any], index: int) -> float | None:
    value = values[index]
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def malformed_provider_response_error() -> MarketDataError:
    return MarketDataError(
        code=MarketDataErrorCode.MALFORMED_PROVIDER_RESPONSE,
        message="Market data provider returned an unexpected response.",
    )
