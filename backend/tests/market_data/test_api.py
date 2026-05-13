from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.deps.auth import require_authenticated_user
from app.main import app
from app.market_data.errors import MarketDataError, MarketDataErrorCode
from app.market_data.schemas import HistoryRange, HistoryResolution
from app.market_data.service import MarketDataService, get_market_data_service

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


class StubProvider:
    def __init__(self) -> None:
        self.search_payload = {
            "result": [
                {
                    "symbol": "AAPL",
                    "displaySymbol": "AAPL",
                    "description": "Apple Inc",
                    "type": "Common Stock",
                }
            ]
        }
        self.quote_payload = {
            "c": 191.25,
            "d": 1.25,
            "dp": 0.66,
            "o": 190.0,
            "h": 193.0,
            "l": 189.5,
            "pc": 190.0,
            "t": 1710000000,
        }
        self.candles_payload = {
            "s": "ok",
            "t": [1709856000, 1709942400],
            "o": [189.0, 190.0],
            "h": [191.0, 192.0],
            "l": [188.0, 189.0],
            "c": [190.0, 191.0],
            "v": [1000, 1200],
        }
        self.search_queries: list[str] = []
        self.quote_symbols: list[str] = []
        self.candle_requests: list[tuple[str, int, int]] = []

    def search_symbols(self, query: str):
        self.search_queries.append(query)
        return self.search_payload

    def get_quote(self, symbol: str):
        self.quote_symbols.append(symbol)
        return self.quote_payload

    def get_daily_candles(self, symbol: str, from_timestamp: int, to_timestamp: int):
        self.candle_requests.append((symbol, from_timestamp, to_timestamp))
        return self.candles_payload


def test_market_data_requires_bearer_authorization():
    response = TestClient(app).get("/api/market-data/symbols/AAPL/quote")

    assert response.status_code == 401
    assert "FINNHUB" not in response.text.upper()


def test_market_data_rejects_non_bearer_authorization():
    response = TestClient(app).get(
        "/api/market-data/symbols/AAPL/quote",
        headers={"Authorization": "Basic nope"},
    )

    assert response.status_code == 401


def test_symbol_search_normalizes_query_and_response():
    provider = StubProvider()

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/search?query=aapl", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "query": "AAPL",
        "results": [
            {
                "symbol": "AAPL",
                "display_symbol": "AAPL",
                "description": "Apple Inc",
                "type": "Common Stock",
            }
        ],
    }
    assert provider.search_queries == ["AAPL"]


def test_latest_quote_success_normalizes_symbol_and_hides_credentials():
    provider = StubProvider()

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/aapl/quote", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "symbol": "AAPL",
        "current_price": 191.25,
        "daily_change": 1.25,
        "daily_percent_change": 0.66,
        "open_price": 190.0,
        "high_price": 193.0,
        "low_price": 189.5,
        "previous_close": 190.0,
        "quote_timestamp": iso_z(1710000000),
    }
    assert provider.quote_symbols == ["AAPL"]
    assert "test-token" not in response.text
    assert "FINNHUB" not in response.text.upper()


def test_latest_quote_unavailable_returns_controlled_not_found():
    provider = StubProvider()
    provider.quote_payload = {
        "c": 0,
        "d": None,
        "dp": None,
        "o": 0,
        "h": 0,
        "l": 0,
        "pc": 0,
        "t": 0,
    }

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/unknown/quote", headers=AUTH_HEADERS)

    assert response.status_code == 404
    assert response.json() == {
        "code": "symbol_not_found",
        "message": "Latest quote data is unavailable for this symbol.",
    }
    assert "Finnhub" not in response.text


def test_latest_quote_rejects_blank_symbol_before_provider_call():
    provider = StubProvider()

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/%20%20/quote", headers=AUTH_HEADERS)

    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_symbol",
        "message": "Ticker symbol is required.",
    }
    assert provider.quote_symbols == []


def test_daily_history_success_uses_daily_resolution_only():
    provider = StubProvider()

    with client_with_provider(provider) as client:
        response = client.get(
            "/api/market-data/symbols/aapl/history?range=1M&resolution=D",
            headers=AUTH_HEADERS,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["range"] == HistoryRange.ONE_MONTH
    assert body["resolution"] == HistoryResolution.DAILY
    assert body["points"][0] == {
        "timestamp": iso_z(1709856000),
        "open_price": 189.0,
        "high_price": 191.0,
        "low_price": 188.0,
        "close_price": 190.0,
        "volume": 1000.0,
    }
    assert provider.candle_requests[0][0] == "AAPL"


def test_history_unavailable_returns_controlled_chart_unavailable():
    provider = StubProvider()
    provider.candles_payload = {"s": "no_data"}

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/aapl/history", headers=AUTH_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "code": "chart_unavailable",
        "message": "Historical chart data is unavailable for this request.",
    }


def test_history_rejects_intraday_resolution_before_provider_call():
    provider = StubProvider()

    with client_with_provider(provider) as client:
        response = client.get(
            "/api/market-data/symbols/aapl/history?resolution=60",
            headers=AUTH_HEADERS,
        )

    assert response.status_code == 422
    assert provider.candle_requests == []


def test_provider_rate_limit_maps_to_stable_response():
    provider = ErrorProvider(
        MarketDataError(
            code=MarketDataErrorCode.RATE_LIMITED,
            message="Market data provider rate limit reached. Please try again later.",
            status_code=429,
        )
    )

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/aapl/quote", headers=AUTH_HEADERS)

    assert response.status_code == 429
    assert response.json() == {
        "code": "rate_limited",
        "message": "Market data provider rate limit reached. Please try again later.",
    }


def test_malformed_provider_response_maps_to_stable_response():
    provider = StubProvider()
    provider.quote_payload = {"c": "not-a-number"}

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/aapl/quote", headers=AUTH_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "code": "malformed_provider_response",
        "message": "Market data provider returned an unexpected response.",
    }


def test_network_failure_maps_to_stable_response_without_raw_error():
    provider = ErrorProvider(
        MarketDataError(
            code=MarketDataErrorCode.PROVIDER_UNAVAILABLE,
            message="Market data provider is temporarily unavailable.",
        )
    )

    with client_with_provider(provider) as client:
        response = client.get("/api/market-data/symbols/aapl/quote", headers=AUTH_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "code": "provider_unavailable",
        "message": "Market data provider is temporarily unavailable.",
    }


class ErrorProvider:
    def __init__(self, error: MarketDataError) -> None:
        self._error = error

    def get_quote(self, symbol: str):
        raise self._error


class client_with_provider:
    def __init__(self, provider: StubProvider | ErrorProvider) -> None:
        self._provider = provider

    def __enter__(self) -> TestClient:
        app.dependency_overrides[get_market_data_service] = lambda: MarketDataService(
            self._provider
        )
        return TestClient(app)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        app.dependency_overrides.pop(get_market_data_service, None)
        app.dependency_overrides.pop(require_authenticated_user, None)


def iso_z(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")
