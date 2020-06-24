from app import db
from app.models.dict_serializable import DictSerializable


class AgentConfig(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    versionDetection = db.Column(
        db.Boolean, default=True
    )  # Enable Version Detection (-sV)
    osDetection = db.Column(db.Boolean, default=True)  # Enable OS Detection (-O)
    enableScripts = db.Column(
        db.Boolean, default=True
    )  # Enable Nmap Scripting Engine (loads all AgentScripts)
    onlyOpens = db.Column(db.Boolean, default=True)  # Only report open ports (--open)
    scanTimeout = db.Column(
        db.Integer, default=660
    )  # SIGKILL nmap if it's running longer than this
    webScreenshots = db.Column(
        db.Boolean, default=True
    )  # Attempt to take web screenshots (aquatone)
    vncScreenshots = db.Column(
        db.Boolean, default=True
    )  # Attempt to take VNC screenshots (xvfb+vncsnapshot)
    webScreenshotTimeout = db.Column(
        db.Integer, default=60
    )  # aquatone process timeout in seconds
    vncScreenshotTimeout = db.Column(
        db.Integer, default=60
    )  # vnc process timeout in seconds

    scriptTimeout = db.Column(db.Integer, default=60)  # --script-timeout (s)
    hostTimeout = db.Column(db.Integer, default=600)  # --host-timeout (s)
    osScanLimit = db.Column(db.Boolean, default=True)  # --osscan-limit
    noPing = db.Column(db.Boolean, default=False)  # -Pn
    udpScan = db.Column(db.Boolean, default=False)  # -sSU
