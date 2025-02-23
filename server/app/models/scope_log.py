from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase
from app.models.dict_serializable import DictSerializable


# Basic Logging for Scope related events
class ScopeLog(NatlasBase, DictSerializable):
    __tablename__ = "scope_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    msg: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __init__(self, msg: str | None = None) -> None:
        self.msg = msg

    def __repr__(self) -> str:
        timerepr = self.created_at.strftime("%Y-%m-%d-%H:%M:%S")
        return f"<Log: {timerepr} - {self.msg[:50]}>"  # type: ignore[index]
