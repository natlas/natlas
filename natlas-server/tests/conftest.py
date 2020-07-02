from app import create_app, db
from app.elastic import ElasticClient
from app.elastic.interface import ElasticInterface
from tests.config import TestConfig

import pytest


@pytest.fixture
def app():
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    return app


@pytest.fixture
def esclient():
    return ElasticClient(TestConfig().ELASTICSEARCH_URL)


@pytest.fixture
def esinterface():
    return ElasticInterface(TestConfig().ELASTICSEARCH_URL)
