import pytest


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
