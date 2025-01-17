from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase, db
from app.models.dict_serializable import DictSerializable

# TODO: This whole table can be replaced with an array field on the AgentConfig table


# Scripts for agents to run
# These will be named according to the command line value that gets passed to nmap
# groups of scripts are also accepted, such as "safe" and "default"
# auth, broadcast, default, discovery, dos, exploit, external, fuzzer, intrusive, malware, safe, version, vuln
# https://nmap.org/book/nse-usage.html#nse-categories


class AgentScript(NatlasBase, DictSerializable):
    __tablename__ = "agent_script"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128), index=True, unique=True)

    @staticmethod
    def get_scripts_string() -> str:
        return ",".join(s.name for s in db.session.scalars(select(AgentScript)).all())  # type: ignore[misc]
