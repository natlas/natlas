from typing import Union
from netaddr import IPAddress
from netaddr.core import AddrFormatError
from .scan_manager import IPScanManager
from .scope_group import ScopeGroup
from datetime import datetime
from flask import current_app


class ScopeManager:

    pendingRescans = []
    dispatchedRescans = []
    scanmanager = None
    init_time = None
    scopes = None
    effective_size = 0

    def init_app(self, app):
        app.ScopeManager = self
        from app.models.scope_item import ScopeItem

        with app.app_context():
            self.scopes = {
                "scope": ScopeGroup("scope", ScopeItem.getScope),
                "blacklist": ScopeGroup("blacklist", ScopeItem.getBlacklist),
            }
        self.init_time = datetime.utcnow()

    def get_scope_size(self) -> int:
        return self.scopes["scope"].size

    def get_blacklist_size(self) -> int:
        return self.scopes["blacklist"].size

    def get_effective_scope_size(self) -> int:
        return self.effective_size

    def get_scope(self) -> list:
        return self.scopes["scope"].list

    def get_blacklist(self) -> list:
        return self.scopes["blacklist"].list

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

    def update_effective_size(self):
        self.effective_size = (
            self.scopes["scope"].set - self.scopes["blacklist"].set
        ).size

    def update_scan_manager(self):

        self.scanmanager = None
        try:
            self.scanmanager = IPScanManager(
                self.scopes["scope"].set,
                self.scopes["blacklist"].set,
                current_app.config["CONSISTENT_SCAN_CYCLE"],
            )
        except Exception as e:
            if self.scanmanager is None or self.scanmanager.get_total() == 0:
                errmsg = "Scan manager could not be instantiated because there was no scope configured."
                current_app.logger.warning(f"{str(datetime.utcnow())} - {errmsg}\n")
            else:
                raise e

    def get_scan_manager(self) -> IPScanManager:
        return self.scanmanager

    def update(self):
        for _, group in self.scopes.items():
            group.update()
        self.update_scan_manager()
        self.update_effective_size()
        current_app.logger.info(f"{str(datetime.utcnow())} - ScopeManager Updated\n")

    def is_acceptable_target(self, target: str) -> bool:
        try:
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        if (
            target in self.scopes["blacklist"].set
            or target not in self.scopes["scope"].set
        ):
            return False

        # Address is in scope and not blacklisted
        return True

    def get_last_cycle_start(self) -> Union[None, datetime]:
        if self.scanmanager is None:
            return None
        else:
            return self.scanmanager.rng.cycle_start_time

    def get_completed_cycle_count(self) -> int:
        if self.scanmanager is None:
            return 0
        else:
            return self.scanmanager.rng.completed_cycle_count
