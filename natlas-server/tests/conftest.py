from app import create_app, db, ScopeManager

from tests.config import TestConfig

import pytest


@pytest.fixture
def app():
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    ScopeManager.update()
    return app
