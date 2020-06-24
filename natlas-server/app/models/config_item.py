from app import db
from app.models.dict_serializable import DictSerializable


# Server configuration options
# This uses a generic key,value style schema so that we can avoid changing the model for every new feature
# Default config options are defined in natlas-server/config.py
class ConfigItem(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    type = db.Column(db.String(256))
    value = db.Column(db.String(256))
