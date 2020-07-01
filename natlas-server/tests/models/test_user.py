import secrets


from app import db
from app.models import User

test_password = secrets.token_urlsafe(16)


def test_new_user(app):
    test_user = User(email="newuser@example.com", is_active=True)
    test_user.set_password(test_password)
    db.session.add(test_user)
    assert test_user.check_password(test_password)
    assert not test_user.check_password("password")
    assert test_user.is_active
    assert not test_user.is_admin
    assert not test_user.password_reset_token
    assert not test_user.password_reset_expiration
    db.session.rollback()


def test_validate_email():
    assert User.validate_email("test@example.com")
    assert User.validate_email("test+extensions@example.com")
    assert User.validate_email("test.extensions@example.com")
    assert not User.validate_email("test")
    assert not User.validate_email("test@")
    assert not User.validate_email("test@example")


def test_reset_token():
    email = "resettoken@example.com"
    user = User(email=email)
    db.session.add(user)
    assert not user.validate_reset_token()
    assert User.get_reset_token(email)
    assert user.validate_reset_token()
    assert User.get_user_by_token(user.password_reset_token)
    user.expire_reset_token()
    assert not user.validate_reset_token()
    assert not User.get_reset_token("notoken@example.com")
    assert not User.get_user_by_token("notoken")
    db.session.rollback()


def test_double_reset_token():
    email = "double_validate@example.com"
    user = User(email=email)
    db.session.add(user)
    assert user.get_reset_token(email)
    assert user.validate_reset_token()
    assert user.validate_reset_token()
    assert user.get_reset_token(email)
    db.session.rollback()
