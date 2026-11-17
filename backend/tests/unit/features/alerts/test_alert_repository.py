from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.features.alerts.repository import AlertRepository, _escape_like


class FakeResult:
    def scalars(self):
        return self

    def all(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.statements: list[object] = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return FakeResult()


def _compile(stmt) -> tuple[str, dict[str, object]]:
    compiled = stmt.compile(dialect=postgresql.dialect())
    return str(compiled), dict(compiled.params)


@pytest.mark.parametrize(
    ("raw", "escaped"),
    [("btc", "btc"), ("100%", "100\\%"), ("a_b", "a\\_b"), ("a\\b", "a\\\\b")],
)
def test_escape_like_neutralizes_wildcards(raw: str, escaped: str) -> None:
    assert _escape_like(raw) == escaped


@pytest.mark.asyncio
async def test_list_query_always_scopes_to_user_and_applies_all_filters() -> None:
    session = RecordingSession()
    repository = AlertRepository(session)  # type: ignore[arg-type]
    user_id = uuid4()

    await repository.list_alerts_for_user(
        user_id, status="paused", scenario="price_below", query="  50%_sol "
    )

    sql, params = _compile(session.statements[0])
    assert "alert_rules.user_id =" in sql
    assert "alert_rules.status =" in sql
    assert "scenario_payload ->> " in sql
    assert "alert_rules.symbol ILIKE" in sql
    assert "alert_rules.name ILIKE" in sql
    assert user_id in params.values()
    assert "paused" in params.values()
    assert "price_below" in params.values()
    assert "%50\\%\\_sol%" in params.values()


@pytest.mark.asyncio
async def test_list_query_without_filters_only_scopes_to_user() -> None:
    session = RecordingSession()
    repository = AlertRepository(session)  # type: ignore[arg-type]

    await repository.list_alerts_for_user(uuid4(), query="   ")

    sql, _ = _compile(session.statements[0])
    assert "alert_rules.user_id =" in sql
    assert "alert_rules.status =" not in sql
    assert "LIKE" not in sql
    assert "scenario_payload ->>" not in sql


@pytest.mark.asyncio
async def test_count_query_ignores_status_and_groups_by_it() -> None:
    session = RecordingSession()
    repository = AlertRepository(session)  # type: ignore[arg-type]

    class CountResult:
        def all(self):
            return [("active", 2), ("paused", 3)]

    async def execute(stmt):
        session.statements.append(stmt)
        return CountResult()

    session.execute = execute  # type: ignore[method-assign]

    counts = await repository.count_alerts_by_status_for_user(
        uuid4(), scenario="coin_news", query="btc"
    )

    sql, _ = _compile(session.statements[0])
    assert counts == {"active": 2, "paused": 3}
    assert "GROUP BY alert_rules.status" in sql
    assert "alert_rules.status =" not in sql
    assert "alert_rules.user_id =" in sql
