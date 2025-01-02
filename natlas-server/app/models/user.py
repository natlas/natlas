import secrets
from datetime import UTC, datetime, timedelta

from email_validator import EmailNotValidError, validate_email
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.models.dict_serializable import DictSerializable
from app.models.token_validation import validate_token


class User(UserMixin, db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    results_per_page = db.Column(db.Integer, default=100)
    preview_length = db.Column(db.Integer, default=100)
    result_format = db.Column(db.Integer, default=0)
    password_reset_token = db.Column(db.String(256), unique=True)
    password_reset_expiration = db.Column(db.DateTime)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    rescans = db.relationship("RescanTask", backref="submitter", lazy="select")
    agents = db.relationship("Agent", backref="user", lazy=True)

    # Tokens expire after 48 hours or upon use
    expiration_duration = 60 * 60 * 24 * 2
    token_length = 32

    def __repr__(self):  # type: ignore[no-untyped-def]
        return f"<User {self.email}>"

    @staticmethod
    def exists(email):  # type: ignore[no-untyped-def]
        return User.query.filter_by(email=email).first() is not None

    # https://github.com/JoshData/python-email-validator
    @staticmethod
    def validate_email(email):  # type: ignore[no-untyped-def]
        try:
            valid = validate_email(email)
            return valid["email"]
        except EmailNotValidError:
            return False

    def set_password(self, password):  # type: ignore[no-untyped-def]
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):  # type: ignore[no-untyped-def]
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):  # type: ignore[no-untyped-def]
        return User.query.get(id)

    def new_reset_token(self):  # type: ignore[no-untyped-def]
        self.password_reset_token = secrets.token_urlsafe(User.token_length)
        self.password_reset_expiration = datetime.now(UTC) + timedelta(
            seconds=User.expiration_duration
        )

    def expire_reset_token(self):  # type: ignore[no-untyped-def]
        self.password_reset_token = None
        self.password_reset_expiration = None

    def validate_reset_token(self):  # type: ignore[no-untyped-def]
        if not (self.password_reset_token and self.password_reset_expiration):
            return False
        return self.password_reset_expiration > datetime.now(UTC)

    @staticmethod
    def get_reset_token(email):  # type: ignore[no-untyped-def]
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        if not user.validate_reset_token():
            user.new_reset_token()
        return user

    @staticmethod
    def get_user_by_token(url_token):  # type: ignore[no-untyped-def]
        if record := User.query.filter_by(password_reset_token=url_token).first():
            return validate_token(
                record,
                url_token,
                record.password_reset_token,
                record.validate_reset_token,
            )
        return False

    @staticmethod
    def new_user_from_invite(invite, password, email=None):  # type: ignore[no-untyped-def]
        user_email = email or invite.email
        new_user = User(email=user_email, is_admin=invite.is_admin, is_active=True)
        new_user.set_password(password)
        invite.accept_invite()
        db.session.add(new_user)
        return new_user
