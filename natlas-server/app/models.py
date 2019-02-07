from time import time
from app import db
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
import jwt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    results_per_page = db.Column(db.Integer, default=100)
    preview_length = db.Column(db.Integer, default=100)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_invite_token(self, expires_in=172800):
        return jwt.encode(
            {'invite_user': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_invite_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['invite_user']
        except:
            return
        return User.query.get(id)


class ScopeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String, index=True, unique=True)
    blacklist = db.Column(db.Boolean, index=True)

    def getBlacklist():
        return ScopeItem.query.filter_by(blacklist=True).all()

    def getScope():
        return ScopeItem.query.filter_by(blacklist=False).all()


class ConfigItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    type = db.Column(db.String(256))
    value = db.Column(db.String(256))

# While generally I prefer to use a singular model name, each record here is going to be storing a set of services
class NatlasServices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sha256 = db.Column(db.String(64))
    services = db.Column(db.Text)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}