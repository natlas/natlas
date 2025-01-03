import os
import tempfile

import pytest
from app import create_app

from tests.config import test_config


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    db_fd, db_name = tempfile.mkstemp()
    test_config.SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_name
    app = create_app(test_config)
    with app.app_context():
        yield app
    os.close(db_fd)
    os.unlink(db_name)


@pytest.fixture
def client(app):  # type: ignore[no-untyped-def]
    with app.test_client() as client:
        yield client
