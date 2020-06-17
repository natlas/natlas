from email_validator import validate_email, EmailNotValidError
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, db
from app.models.dict_serializable import DictSerializable
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
	rescans = db.relationship('RescanTask', backref='submitter', lazy='select')
	agents = db.relationship('Agent', backref='user', lazy=True)

	password_reset_token = db.Column(db.String(32), unique=True)
	password_reset_expiration = db.Column(db.DateTime)
	creation_date = db.Column(db.DateTime, default=utcnow_tz)
	is_active = db.Column(db.Boolean, default=False)

	# Tokens expire after 48 hours or upon use
	expiration_duration = 60 * 60 * 24 * 2
	token_length = 32

	def __repr__(self):
		return '<User {}>'.format(self.email)

	# https://github.com/JoshData/python-email-validator
	@staticmethod
	def validate_email(email):
		try:
			valid = validate_email(email)
			email = valid["email"]
			return email
		except EmailNotValidError:
			return False

	# This is really only used by the add-user bootstrap script, but useful to contain it here.
	@staticmethod
	def generate_password(length):
		passcharset = string.ascii_uppercase + string.ascii_lowercase + string.digits
		return ''.join(secrets.choice(passcharset) for i in range(16))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	@login.user_loader
	def load_user(id):
		return User.query.get(int(id))

	def new_reset_token(self):
		self.password_reset_token = secrets.token_urlsafe(User.token_length)
		self.password_reset_expiration = utcnow_tz() + timedelta(seconds=User.expiration_duration)

	def expire_reset_token(self):
		self.password_reset_token = None
		self.password_reset_expiration = None

	def validate_reset_token(self):
		now = utcnow_tz()
		if self.password_reset_expiration > now:
			return True
		else:
			return False

	@staticmethod
	def get_user_by_token(url_token):
		token_user = User.query.filter_by(token=url_token).first()
		if token_user and secrets.compare_digest(url_token, token_user.password_reset_token) and token_user.validate_reset_token():
			return token_user
		else:
			# still do a digest compare of equal sizes to resist timing attacks
			secrets.compare_digest(url_token, secrets.token_urlsafe(User.token_length))
			return False
