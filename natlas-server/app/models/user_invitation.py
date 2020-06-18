from app import db
from app.util import utcnow_tz
import secrets
from datetime import timedelta, datetime
from app.models.dict_serializable import DictSerializable


class UserInvitation(db.Model, DictSerializable):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(128), unique=True)
	token = db.Column(db.String(32), unique=True, nullable=False)
	creation_date = db.Column(db.DateTime, default=utcnow_tz)
	expiration_date = db.Column(db.DateTime, nullable=False)
	accepted_date = db.Column(db.DateTime)
	is_expired = db.Column(db.Boolean, default=False)
	# is_admin should really only be used for bootstrapping users with add-user.py
	is_admin = db.Column(db.Boolean, default=False)

	# Tokens expire after 48 hours or upon use
	expiration_duration = 60 * 60 * 24 * 2
	token_length = 32

	# Build a new invitation
	@staticmethod
	def new_invite(email=None, is_admin=False):
		now = datetime.utcnow()
		expiration_date = now + timedelta(seconds=UserInvitation.expiration_duration)
		new_token = secrets.token_urlsafe(UserInvitation.token_length)
		invite = UserInvitation.query.filter_by(email=email).first()
		if invite and not invite.accepted_date:
			invite.token = new_token
			invite.expiration_date = expiration_date
		else:
			invite = UserInvitation(email=email, token=new_token, is_admin=is_admin, expiration_date=expiration_date)
			db.session.add(invite)
		return invite

	# Get invite from database in (roughly) constant time
	@staticmethod
	def get_invite(url_token):
		db_token = UserInvitation.query.filter_by(token=url_token).first()
		if db_token and secrets.compare_digest(url_token, db_token.token) and db_token.validate_invite():
			return db_token
		else:
			# still do a digest compare of equal sizes to resist timing attacks
			secrets.compare_digest(url_token, secrets.token_urlsafe(UserInvitation.token_length))
			return False

	def accept_invite(self):
		now = datetime.utcnow()
		self.accepted_date = now
		self.expire_invite(now)

	# If a token is expired, mark it as such
	def expire_invite(self, timestamp):
		if self.expiration_date < timestamp:
			# Leave original expiration date in tact since it's already past
			self.is_expired = True
		else:
			# Mark now as the expiration because it's been redeemed
			self.expiration_date = timestamp
			self.is_expired = True

	# verify that the token is not expired
	def validate_invite(self):
		now = datetime.utcnow()
		if self.expiration_date > now and not self.is_expired:
			return True
		else:
			return False
