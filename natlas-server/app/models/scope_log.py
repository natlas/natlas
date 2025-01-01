from datetime import datetime

from app import db
from app.models.dict_serializable import DictSerializable


# Basic Logging for Scope related events
class ScopeLog(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, msg=None):  # type: ignore[no-untyped-def]
        self.msg = msg

    def __repr__(self):  # type: ignore[no-untyped-def]
        timerepr = self.created_at.strftime("%Y-%m-%d-%H:%M:%S")
        return f"<Log: {timerepr} - {self.msg[:50]}>"
