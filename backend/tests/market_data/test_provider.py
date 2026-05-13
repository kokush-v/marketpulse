from dataclasses import dataclass

from fastapi import status

from app.core.config import Settings
from app.market_data.errors import MarketDataError, MarketDataErrorCode
from app.market_data.provider import FinnhubProvider


def test_finnhub_provider_calls_official_sdk_methods():
    sdk_client = StubFinnhubSdkClient()
    provider = FinnhubProvider(settings(), sdk_client=sdk_client)

    assert provider.search_symbols("AAPL") == {"result": []}
    assert provider.get_quote("AAPL") == {"c": 191.25}
    assert provider.get_daily_candles("AAPL", 1, 2) == {"s": "ok"}

    assert sdk_client.calls == [
        ("symbol_lookup", "AAPL"),
        ("quote", "AAPL"),
        ("stock_candles", "AAPL", "D", 1, 2),
    ]


def test_finnhub_provider_requires_api_key_when_sdk_client_not_injected():
    provider = FinnhubProvider(settings(api_key=None))

    try:
        provider.get_quote("AAPL")
    except MarketDataError as exc:
        assert exc.code == MarketDataErrorCode.PROVIDER_UNCONFIGURED
        assert "secret" not in exc.message.lower()
    else:
        raise AssertionError("Expected provider configuration error.")


def test_finnhub_provider_maps_sdk_rate_limit_without_raw_error():
    provider = FinnhubProvider(
        settings(),
        sdk_client=FailingSdkClient(status.HTTP_429_TOO_MANY_REQUESTS),
    )

    try:
        provider.get_quote("AAPL")
    except MarketDataError as exc:
        assert exc.code == MarketDataErrorCode.RATE_LIMITED
        assert exc.status_code == 429
        assert "token" not in exc.message.lower()
    else:
        raise AssertionError("Expected rate-limit error.")


def test_finnhub_provider_maps_sdk_access_denied_to_chart_unavailable():
    provider = FinnhubProvider(settings(), sdk_client=FailingSdkClient(status.HTTP_403_FORBIDDEN))

    try:
        provider.get_daily_candles("AAPL", 1, 2)
    except MarketDataError as exc:
        assert exc.code == MarketDataErrorCode.CHART_UNAVAILABLE
    else:
        raise AssertionError("Expected chart-unavailable error.")


def test_finnhub_provider_maps_non_mapping_payload_to_malformed_response():
    provider = FinnhubProvider(settings(), sdk_client=NonMappingSdkClient())

    try:
        provider.get_quote("AAPL")
    except MarketDataError as exc:
        assert exc.code == MarketDataErrorCode.MALFORMED_PROVIDER_RESPONSE
    else:
        raise AssertionError("Expected malformed provider response.")


@dataclass(frozen=True)
class StubResponse:
    status_code: int


class StubFinnhubSdkClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def symbol_lookup(self, query: str):
        self.calls.append(("symbol_lookup", query))
        return {"result": []}

    def quote(self, symbol: str):
        self.calls.append(("quote", symbol))
        return {"c": 191.25}

    def stock_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int):
        self.calls.append(("stock_candles", symbol, resolution, from_timestamp, to_timestamp))
        return {"s": "ok"}


class FailingSdkClient:
    def __init__(self, status_code: int) -> None:
        self._status_code = status_code

    def quote(self, symbol: str):
        raise FakeFinnhubApiException(self._status_code)

    def stock_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int):
        raise FakeFinnhubApiException(self._status_code)


class NonMappingSdkClient:
    def quote(self, symbol: str):
        return []


class FakeFinnhubApiException(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__("raw provider message with token=secret")
        self.response = StubResponse(status_code=status_code)


def settings(api_key: str | None = "test-key") -> Settings:
    return Settings(
        app_name="MarketPulse API",
        app_version="0.1.0",
        database_url="postgresql+psycopg://marketpulse:marketpulse@localhost:5432/marketpulse",
        finnhub_api_base_url="https://finnhub.example.test",
        finnhub_api_key=api_key,
    )
