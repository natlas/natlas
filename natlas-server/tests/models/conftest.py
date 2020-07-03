import pytest

from app import db


@pytest.fixture(autouse=True)
def session_rollback(app):
    db.session.rollback()
