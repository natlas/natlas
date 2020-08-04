import tempfile
import os
from app import create_app

from tests.config import TestConfig

import pytest


@pytest.fixture
def app():
    conf = TestConfig()
    db_fd, db_name = tempfile.mkstemp()
    conf.SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_name
    app = create_app(conf)
    with app.app_context():
        yield app
    os.close(db_fd)
    os.unlink(db_name)


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
