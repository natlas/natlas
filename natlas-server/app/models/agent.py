from app import db
from app.util import utcnow_tz, generate_hex_16
import string
import secrets
from app.models.dict_serializable import DictSerializable


# Agent registration
# Users can have many agents, each agent has an ID and a secret (token)
# Friendly name is purely for identification of agents in the management page
class Agent(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # agent identification string for storing in reports
    agentid = db.Column(db.String(16), index=True, unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=utcnow_tz)
    # auth token
    token = db.Column(db.String(32), index=True, unique=True)
    # optional friendly name for viewing on user page
    friendly_name = db.Column(db.String(32), default="")

    def verify_secret(self, secret):
        return secrets.compare_digest(secret, self.token)

    @staticmethod
    def verify_agent(auth_header):
        auth_list = auth_header.split()
        if auth_list[0].lower() != "bearer":
            return False
        agent_id, agent_token = auth_list[1].split(":", 1)
        agent = Agent.load_agent(agent_id)
        return bool(agent and agent.verify_secret(agent_token))

    @staticmethod
    def load_agent(agentid):
        return Agent.query.filter_by(agentid=agentid).first()

    @staticmethod
    def generate_token():
        tokencharset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return "".join(secrets.choice(tokencharset) for _ in range(32))

    @staticmethod
    def generate_agentid():
        return generate_hex_16()
