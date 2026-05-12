from os import getenv

import pytest

from app.db.session import check_database_connection, create_database_engine


def test_database_connection_helper_reports_live_database_when_enabled():
    if getenv("RUN_DATABASE_TESTS") != "true":
        pytest.skip("Set RUN_DATABASE_TESTS=true to run the live database smoke test.")

    engine = create_database_engine()

    try:
        assert check_database_connection(engine)
    finally:
        engine.dispose()

