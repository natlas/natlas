from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase, db
from app.models.dict_serializable import DictSerializable

if TYPE_CHECKING:
    pass


# Rescan Queue
# Each record represents a user-requested rescan of a given target.
# Tracks when it was dispatched, when it was completed, and the scan id of the complete scan.
class RescanTask(NatlasBase, DictSerializable):
    __tablename__ = "rescan_task"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_added: Mapped[datetime] = mapped_column(index=True, default=datetime.utcnow())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    target: Mapped[str] = mapped_column(String(128), index=True)
    dispatched: Mapped[bool | None] = mapped_column(default=False, index=True)
    date_dispatched: Mapped[datetime | None] = mapped_column(index=True)
    complete: Mapped[bool | None] = mapped_column(default=False, index=True)
    date_completed: Mapped[datetime | None] = mapped_column(index=True)
    scan_id: Mapped[str | None] = mapped_column(String(128), index=True, unique=True)

    def dispatchTask(self) -> None:
        self.dispatched = True
        self.date_dispatched = datetime.utcnow()

    def completeTask(self, scan_id: str) -> None:
        self.scan_id = scan_id
        self.complete = True
        self.date_completed = datetime.utcnow()

    @staticmethod
    def getPendingTasks() -> list["RescanTask"]:
        # Tasks that haven't been completed and haven't been dispatched
        return list(
            db.session.scalars(
                select(RescanTask).where(
                    RescanTask.complete == False, RescanTask.dispatched == False
                )
            ).all()
        )

    @staticmethod
    def getDispatchedTasks() -> list["RescanTask"]:
        # Tasks that have been dispatched but haven't been completed
        return list(
            db.session.scalars(
                select(RescanTask).where(
                    RescanTask.dispatched == True, RescanTask.complete == False
                )
            ).all()
        )

    @staticmethod
    def getIncompleteTasks() -> list["RescanTask"]:
        # All tasks that haven't been marked as complete
        return list(
            db.session.scalars(
                select(RescanTask).where(RescanTask.complete == False)
            ).all()
        )

    @staticmethod
    def getIncompleteTaskForTarget(ip: str) -> list["RescanTask"]:
        return list(
            db.session.scalars(
                select(RescanTask).where(
                    RescanTask.target == ip, RescanTask.complete == False
                )
            ).all()
        )
