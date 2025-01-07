from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase
from app.models.dict_serializable import DictSerializable


# Server configuration options
# This uses a generic key,value style schema so that we can avoid changing the model for every new feature
# Default config options are defined in natlas-server/config.py
class ConfigItem(NatlasBase, DictSerializable):
    __tablename__ = "config_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(256), unique=True)
    type: Mapped[str | None] = mapped_column(String(256))
    value: Mapped[str | None] = mapped_column(String(256))
