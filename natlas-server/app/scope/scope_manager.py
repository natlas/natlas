from datetime import datetime

from flask import current_app
from netaddr import IPAddress
from netaddr.core import AddrFormatError

from .scan_group import ScanGroup
from .scan_manager import IPScanManager


class ScopeManager:
    pendingRescans = []
    dispatchedRescans = []
    scanmanager = None
    init_time = None
    scopes = None
    effective_size = 0
    default_group = "all"

    def init_app(self, app):
        app.ScopeManager = self

        with app.app_context():
            self.scopes = {
                ScopeManager.default_group: ScanGroup(
                    scope=ScopeManager.default_group,
                    blacklist=ScopeManager.default_group,
                )
            }
        self.init_time = datetime.utcnow()

    def load_all_groups(self):
        """
        Used at initialization to update all scan groups with their database values
        """
        for _, group in self.scopes.items():
            group.update()

    def get_scope_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_scope_size()

    def get_blacklist_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_blacklist_size()

    def get_effective_scope_size(self, group: str = default_group) -> int:
        return self.scopes[group].get_effective_size()

    def get_scope(self, group: str = default_group) -> list:
        return self.scopes[group].scope.list

    def get_blacklist(self, group: str = default_group) -> list:
        return self.scopes[group].blacklist.list

    def get_scan_manager(self, group: str = default_group) -> IPScanManager:
        return self.scopes.get(group).get_scan_manager()

    def get_last_cycle_start(self, group: str = default_group) -> datetime:
        return self.scopes[group].get_last_cycle_start()

    def get_completed_cycle_count(self, group: str = default_group) -> int:
        return self.scopes[group].get_completed_cycle_count()

    def update(self, group: str = default_group):
        self.scopes.get(group).update()
        current_app.logger.info(f"{str(datetime.utcnow())} - ScopeManager Updated\n")

    def is_acceptable_target(self, target: str, group: str = default_group) -> bool:
        try:
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        if (
            target in self.scopes[group].blacklist.set
            or target not in self.scopes[group].scope.set
        ):
            return False

        # Address is in scope and not blacklisted
        return True

    def get_pending_rescans(self) -> list:
        return self.pendingRescans

    def get_dispatched_rescans(self) -> list:
        return self.dispatchedRescans

    def get_incomplete_scans(self) -> list:
        if self.pendingRescans == [] or self.dispatchedRescans == []:
            from app.models import RescanTask

            self.pendingRescans = RescanTask.getPendingTasks()
            self.dispatchedRescans = RescanTask.getDispatchedTasks()
        return self.pendingRescans + self.dispatchedRescans

    def update_dispatched_rescans(self):
        from app.models import RescanTask

        self.dispatchedRescans = RescanTask.getDispatchedTasks()

    def update_pending_rescans(self):
        from app.models import RescanTask

        self.pendingRescans = RescanTask.getPendingTasks()
