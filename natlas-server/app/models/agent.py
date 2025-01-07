import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.models.dict_serializable import DictSerializable
from app.util import generate_hex_16


# Agent registration
# Users can have many agents, each agent has an ID and a secret (token)
# Friendly name is purely for identification of agents in the management page
class Agent(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    agentid: Mapped[str] = mapped_column(String(128), index=True, unique=True)
    date_created: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    token: Mapped[str | None] = mapped_column(String(128), index=True, unique=True)
    friendly_name: Mapped[str | None] = mapped_column(String(128), default="")

    def verify_secret(self, secret: str) -> bool:
        return secrets.compare_digest(secret, self.token)  # type: ignore[type-var]

    @staticmethod
    def verify_agent(auth_header: str) -> bool:
        auth_list = auth_header.split()
        if auth_list[0].lower() != "bearer":
            return False
        agent_id, agent_token = auth_list[1].split(":", 1)
        agent = Agent.load_agent(agent_id)
        return bool(agent is not None and agent.verify_secret(agent_token))

    @staticmethod
    def load_agent(agentid: str) -> Optional["Agent"]:
        return db.session.scalars(select(Agent).where(Agent.agentid == agentid)).first()

    @staticmethod
    def generate_token() -> str:
        tokencharset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return "".join(secrets.choice(tokencharset) for _ in range(32))

    @staticmethod
    def generate_agentid() -> str:
        return generate_hex_16()
