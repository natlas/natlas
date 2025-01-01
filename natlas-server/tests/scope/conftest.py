import pytest
from app import db


@pytest.fixture(autouse=True)
def session_rollback(app):  # type: ignore[no-untyped-def]
    db.session.rollback()
