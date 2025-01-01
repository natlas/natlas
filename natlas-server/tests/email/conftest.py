import pytest


@pytest.fixture
def app_no_email(app):  # type: ignore[no-untyped-def]
    app.config.update(
        {"MAIL_SERVER": None, "MAIL_FROM": None, "SERVER_NAME": "example.com"}
    )
    yield app
