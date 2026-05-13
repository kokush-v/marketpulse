from collections.abc import Mapping
from typing import Any

import finnhub
from fastapi import status
from finnhub.exceptions import FinnhubAPIException, FinnhubRequestException

from app.core.config import Settings
from app.market_data.errors import (
    MarketDataError,
    MarketDataErrorCode,
    provider_unconfigured_error,
)

JsonObject = Mapping[str, Any]


class FinnhubProvider:
    def __init__(self, settings: Settings, sdk_client: Any | None = None) -> None:
        self._settings = settings
        self._sdk_client = sdk_client

    def search_symbols(self, query: str) -> JsonObject:
        return self._call_provider(lambda client: client.symbol_lookup(query))

    def get_quote(self, symbol: str) -> JsonObject:
        return self._call_provider(lambda client: client.quote(symbol))

    def get_daily_candles(self, symbol: str, from_timestamp: int, to_timestamp: int) -> JsonObject:
        return self._call_provider(
            lambda client: client.stock_candles(symbol, "D", from_timestamp, to_timestamp)
        )

    def _call_provider(self, call: Any) -> JsonObject:
        try:
            payload = call(self._get_sdk_client())
        except MarketDataError:
            raise
        except FinnhubAPIException as exc:
            raise self._map_api_exception(exc) from exc
        except FinnhubRequestException as exc:
            raise MarketDataError(
                code=MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                message="Market data provider is temporarily unavailable.",
            ) from exc
        except Exception as exc:
            if get_exception_status_code(exc) is not None:
                raise self._map_api_exception(exc) from exc
            raise MarketDataError(
                code=MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                message="Market data provider is temporarily unavailable.",
            ) from exc

        if not isinstance(payload, Mapping):
            raise MarketDataError(
                code=MarketDataErrorCode.MALFORMED_PROVIDER_RESPONSE,
                message="Market data provider returned an unexpected response.",
            )

        return payload

    def _get_sdk_client(self) -> Any:
        if self._sdk_client is not None:
            return self._sdk_client

        if not self._settings.finnhub_api_key:
            raise provider_unconfigured_error()

        self._sdk_client = finnhub.Client(api_key=self._settings.finnhub_api_key)
        self._sdk_client.API_URL = self._settings.finnhub_api_base_url.rstrip("/")
        return self._sdk_client

    def _map_api_exception(self, exc: BaseException) -> MarketDataError:
        status_code = get_exception_status_code(exc)
        if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise MarketDataError(
                code=MarketDataErrorCode.RATE_LIMITED,
                message="Market data provider rate limit reached. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
            raise MarketDataError(
                code=MarketDataErrorCode.CHART_UNAVAILABLE,
                message="Historical chart data is unavailable for this request.",
            )

        if status_code is not None and status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise MarketDataError(
                code=MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                message="Market data provider is temporarily unavailable.",
            )

        return MarketDataError(
            code=MarketDataErrorCode.PROVIDER_UNAVAILABLE,
            message="Market data provider could not complete the request.",
        )


def get_exception_status_code(exc: BaseException) -> int | None:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    response = getattr(exc, "response", None)
    response_status_code = getattr(response, "status_code", None)
    if isinstance(response_status_code, int):
        return response_status_code

    return None
