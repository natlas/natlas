from app import create_app, db

from tests.config import TestConfig

import pytest


@pytest.fixture
def app_no_email():
    app = create_app(TestConfig)
    app.config.update(
        {"MAIL_SERVER": None, "MAIL_FROM": None, "SERVER_NAME": "example.com"}
    )
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    return app
