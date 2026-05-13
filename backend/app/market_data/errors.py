from enum import StrEnum

from fastapi import status


class MarketDataErrorCode(StrEnum):
    INVALID_SYMBOL = "invalid_symbol"
    PROVIDER_UNCONFIGURED = "provider_unconfigured"
    SYMBOL_NOT_FOUND = "symbol_not_found"
    RATE_LIMITED = "rate_limited"
    CHART_UNAVAILABLE = "chart_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    MALFORMED_PROVIDER_RESPONSE = "malformed_provider_response"


class MarketDataError(Exception):
    def __init__(
        self,
        code: MarketDataErrorCode,
        message: str,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def provider_unconfigured_error() -> MarketDataError:
    return MarketDataError(
        code=MarketDataErrorCode.PROVIDER_UNCONFIGURED,
        message="Market data provider is not configured.",
    )
