from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.models.dict_serializable import DictSerializable


# Scripts for agents to run
# These will be named according to the command line value that gets passed to nmap
# groups of scripts are also accepted, such as "safe" and "default"
# auth, broadcast, default, discovery, dos, exploit, external, fuzzer, intrusive, malware, safe, version, vuln
# https://nmap.org/book/nse-usage.html#nse-categories
class AgentScript(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128), index=True, unique=True)

    @staticmethod
    def get_scripts_string() -> str:
        return ",".join(s.name for s in AgentScript.query.all())
