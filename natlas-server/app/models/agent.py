from app import db
from app.util import utcnow_tz, generate_hex_16
import string
import random
from app.models.dict_serializable import DictSerializable


# Agent registration
# Users can have many agents, each agent has an ID and a secret (token)
# Friendly name is purely for identification of agents in the management page
class Agent(db.Model, DictSerializable):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	# agent identification string for storing in reports
	agentid = db.Column(db.String(16), index=True, unique=True, nullable=False)
	date_created = db.Column(db.DateTime, nullable=False, default=utcnow_tz)
	# auth token
	token = db.Column(db.String(32), index=True, unique=True)
	# optional friendly name for viewing on user page
	friendly_name = db.Column(db.String(32), default="")

	def verify_token(self, token):
		if self.token == token:
			return True
		return False

	@staticmethod
	def load_agent(agentid):
		return Agent.query.filter_by(agentid=agentid).first()

	@staticmethod
	def generate_token():
		tokencharset = string.ascii_uppercase + string.ascii_lowercase + string.digits
		return ''.join(random.choice(tokencharset) for _ in range(32))

	@staticmethod
	def generate_agentid():
		return generate_hex_16()
