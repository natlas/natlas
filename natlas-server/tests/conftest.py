from app import create_app, db

from tests.config import TestConfig

import pytest


@pytest.fixture
def app():
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    return app
