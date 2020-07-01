from app import db
from app.models.dict_serializable import DictSerializable
from datetime import datetime


# Basic Logging for Scope related events
class ScopeLog(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, msg=None):
        self.msg = msg

    def __repr__(self):
        timerepr = self.created_at.strftime("%Y-%m-%d-%H:%M:%S")
        return f"<Log: {timerepr} - {self.msg[:50]}>"
