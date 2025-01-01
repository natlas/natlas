from app import db
from app.models.dict_serializable import DictSerializable


# Scripts for agents to run
# These will be named according to the command line value that gets passed to nmap
# groups of scripts are also accepted, such as "safe" and "default"
# auth, broadcast, default, discovery, dos, exploit, external, fuzzer, intrusive, malware, safe, version, vuln
# https://nmap.org/book/nse-usage.html#nse-categories
class AgentScript(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)

    @staticmethod
    def get_scripts_string():  # type: ignore[no-untyped-def]
        return ",".join(s.name for s in AgentScript.query.all())
