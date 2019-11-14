from email_validator import validate_email, EmailNotValidError
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, db


class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(128), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	is_admin = db.Column(db.Boolean, default=False)
	results_per_page = db.Column(db.Integer, default=100)
	preview_length = db.Column(db.Integer, default=100)
	result_format = db.Column(db.Integer, default=0)
	rescans = db.relationship('RescanTask', backref='submitter', lazy='select')
	agents = db.relationship('Agent', backref='user', lazy=True)
	tokens = db.relationship('EmailToken', backref='user', lazy=True)

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
		return ''.join(random.SystemRandom().choice(passcharset) for _ in range(length))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	@login.user_loader
	def load_user(id):
		return User.query.get(int(id))

	def get_reset_password_token(self, expires_in=600):
		from app.models import EmailToken
		newToken = EmailToken.new_token(user_id=self.id, token_type='reset', expires_in=expires_in)
		return newToken.token

	@staticmethod
	def verify_reset_password_token(token):
		from app.models import EmailToken
		myToken = EmailToken.get_token(token)
		if myToken and myToken.verify_token('reset'):
			return User.query.get(myToken.user_id)
		else:
			return False

	# 172800 seconds == 48 hours
	def get_invite_token(self, expires_in=172800):
		from app.models import EmailToken
		newToken = EmailToken.new_token(user_id=self.id, token_type='invite', expires_in=expires_in)
		return newToken.token

	@staticmethod
	def verify_invite_token(token):
		from app.models import EmailToken
		myToken = EmailToken.get_token(token)
		if myToken and myToken.verify_token('invite'):
			return User.query.get(myToken.user_id)
		else:
			return False

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
