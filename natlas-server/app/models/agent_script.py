from app import db
from app.models.dict_serializable import DictSerializable


# Scripts for agents to run
# These will be named according to the command line value that gets passed to nmap
# groups of scripts are also accepted, such as "safe" and "default"
# auth, broadcast, default, discovery, dos, exploit, external, fuzzer, intrusive, malware, safe, version, vuln
# https://nmap.org/book/nse-usage.html#nse-categories
class AgentScript(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True)

    @staticmethod
    def getScriptsString(scriptList=None):
        if scriptList:  # optionally pass in existing query and convert to string
            return ",".join(s.name for s in scriptList)
        return ",".join(s.name for s in AgentScript.query.all())
