from app import create_app, db

from tests.config import TestConfig

import pytest


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
