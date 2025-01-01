import pytest


@pytest.fixture
def runner(app):  # type: ignore[no-untyped-def]
    return app.test_cli_runner()
