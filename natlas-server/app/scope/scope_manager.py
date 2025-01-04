from datetime import datetime
from typing import TYPE_CHECKING

from flask import current_app
from netaddr import IPAddress
from netaddr.core import AddrFormatError

from app.scope.scan_group import ScanGroup
from app.scope.scan_manager import IPScanManager

if TYPE_CHECKING:
    from app.models.rescan_task import RescanTask


class ScopeManager:
    scanmanager = None  # type: ignore[var-annotated]
    init_time = None  # type: ignore[var-annotated]
    scopes = None  # type: ignore[var-annotated]
    effective_size = 0
    default_group = "all"

    def __init__(self) -> None:
        self.pendingRescans: list[RescanTask] = []
        self.dispatchedRescans: list[RescanTask] = []

    def init_app(self, app):  # type: ignore[no-untyped-def]
        app.ScopeManager = self

        with app.app_context():
            self.scopes = {
                ScopeManager.default_group: ScanGroup(
                    scope=ScopeManager.default_group,
                    blacklist=ScopeManager.default_group,
                )
            }
        self.init_time = datetime.utcnow()

    def load_all_groups(self) -> None:
        """
        Used at initialization to update all scan groups with their database values
        """
        for _, group in self.scopes.items():  # type: ignore[union-attr]
            group.update()

    def get_scope_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_scope_size()  # type: ignore[index, no-any-return]

    def get_blacklist_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_blacklist_size()  # type: ignore[index, no-any-return]

    def get_effective_scope_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_effective_size()  # type: ignore[index, no-any-return]

    def get_scope(self, group: str = default_group) -> list:  # type: ignore[type-arg]
        return self.scopes[group].scope.list  # type: ignore[index, no-any-return]

    def get_blacklist(self, group: str = default_group) -> list:  # type: ignore[type-arg]
        return self.scopes[group].blacklist.list  # type: ignore[index, no-any-return]

    def get_scan_manager(self, group: str = default_group) -> IPScanManager:
        return self.scopes.get(group).get_scan_manager()  # type: ignore[no-any-return, union-attr]

    def get_last_cycle_start(self, group: str = default_group) -> datetime:
        return self.scopes[group].get_last_cycle_start()  # type: ignore[index, no-any-return]

    def get_completed_cycle_count(self, group: str = default_group) -> int:
        return self.scopes[group].get_completed_cycle_count()  # type: ignore[index, no-any-return]

    def update(self, group: str = default_group) -> None:
        self.scopes.get(group).update()  # type: ignore[union-attr]
        current_app.logger.info(f"{datetime.utcnow()!s} - ScopeManager Updated\n")

    def is_acceptable_target(self, target: str, group: str = default_group) -> bool:
        try:
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        return (
            target not in self.scopes[group].blacklist.set  # type: ignore[index]
            and target in self.scopes[group].scope.set  # type: ignore[index]
        )

    def get_pending_rescans(self) -> list["RescanTask"]:
        return self.pendingRescans

    def get_dispatched_rescans(self) -> list["RescanTask"]:
        return self.dispatchedRescans

    def get_incomplete_scans(self) -> list["RescanTask"]:
        if self.pendingRescans == [] or self.dispatchedRescans == []:
            from app.models import RescanTask

            self.pendingRescans = RescanTask.getPendingTasks()
            self.dispatchedRescans = RescanTask.getDispatchedTasks()
        return self.pendingRescans + self.dispatchedRescans

    def update_dispatched_rescans(self) -> None:
        from app.models import RescanTask

        self.dispatchedRescans = RescanTask.getDispatchedTasks()

    def update_pending_rescans(self) -> None:
        from app.models import RescanTask

        self.pendingRescans = RescanTask.getPendingTasks()
