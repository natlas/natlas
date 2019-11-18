from email_validator import validate_email, EmailNotValidError
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, db
from app.models.dict_serializable import DictSerializable


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

	def new_token(self, token_type):
		from app.models import EmailToken
		newToken = EmailToken.new_token(user_id=self.id, token_type=token_type)
		return newToken.token

	@staticmethod
	def verify_token(token, token_type):
		from app.models import EmailToken
		myToken = EmailToken.get_token(token)
		if myToken and myToken.verify_token(token_type):
			return User.query.get(myToken.user_id)
		else:
			return False
