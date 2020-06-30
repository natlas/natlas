from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, db
from app.models.dict_serializable import DictSerializable
from app.models.token_validation import validate_token
import secrets
from app.util import utcnow_tz
from datetime import timedelta


class User(UserMixin, db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    results_per_page = db.Column(db.Integer, default=100)
    preview_length = db.Column(db.Integer, default=100)
    result_format = db.Column(db.Integer, default=0)
    password_reset_token = db.Column(db.String(32), unique=True)
    password_reset_expiration = db.Column(db.DateTime)
    creation_date = db.Column(db.DateTime, default=utcnow_tz)
    is_active = db.Column(db.Boolean, default=False)
    rescans = db.relationship("RescanTask", backref="submitter", lazy="select")
    agents = db.relationship("Agent", backref="user", lazy=True)

    # Tokens expire after 48 hours or upon use
    expiration_duration = 60 * 60 * 24 * 2
    token_length = 32

    def __repr__(self):
        return f"<User {self.email}>"

    # https://github.com/JoshData/python-email-validator
    @staticmethod
    def validate_email(email):
        try:
            valid = validate_email(email)
            email = valid["email"]
            return email
        except EmailNotValidError:
            return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(id)

    def new_reset_token(self):
        self.password_reset_token = secrets.token_urlsafe(User.token_length)
        self.password_reset_expiration = utcnow_tz() + timedelta(
            seconds=User.expiration_duration
        )

    def expire_reset_token(self):
        self.password_reset_token = None
        self.password_reset_expiration = None

    def validate_reset_token(self):
        now = utcnow_tz()
        return self.password_reset_expiration > now

    @staticmethod
    def get_reset_token(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        if not user.validate_reset_token():
            user.new_reset_token()
        return user

    @staticmethod
    def get_user_by_token(url_token):
        record = User.query.filter_by(password_reset_token=url_token).first()
        return validate_token(
            record, url_token, record.password_reset_token, record.validate_reset_token
        )

    @staticmethod
    def new_user_from_invite(invite, password, email=None):
        user_email = email if email else invite.email
        new_user = User(email=user_email, is_admin=invite.is_admin, is_active=True)
        new_user.set_password(password)
        invite.accept_invite()
        db.session.add(new_user)
        return new_user
