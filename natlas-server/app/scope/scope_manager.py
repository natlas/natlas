from typing import Union
from netaddr import IPNetwork, IPAddress, IPSet
from netaddr.core import AddrFormatError
from .scan_manager import IPScanManager
from datetime import datetime
from flask import current_app


class ScopeManager:

    lists = {"scope": [], "blacklist": []}
    sets = {"scope": IPSet(), "blacklist": IPSet()}
    sizes = {"scope": 0, "blacklist": 0, "effective": 0}
    pendingRescans = []
    dispatchedRescans = []
    scanmanager = None
    init_time = None

    def __init__(self):
        self.init_time = datetime.utcnow()

    def get_scope_size(self) -> int:
        return self.sizes["scope"]

    def get_blacklist_size(self) -> int:
        return self.sizes["blacklist"]

    def get_effective_scope_size(self) -> int:
        return self.sizes["effective"]

    def get_scope(self) -> list:
        return self.lists["scope"]

    def get_blacklist(self) -> list:
        return self.lists["blacklist"]

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

    def update_scope(self, blacklist: bool = True):
        from app.models import ScopeItem

        selector = "blacklist" if blacklist else "scope"
        items = ScopeItem.getBlacklist() if blacklist else ScopeItem.getScope()
        self.lists[selector] = [IPNetwork(item.target, False) for item in items]
        self.sets[selector] = IPSet(self.lists[selector])
        self.sizes[selector] = self.sets[selector].size

    def update_scan_manager(self):

        self.scanmanager = None
        try:
            self.scanmanager = IPScanManager(
                self.sets["scope"],
                self.sets["blacklist"],
                current_app.config["CONSISTENT_SCAN_CYCLE"],
            )
        except Exception as e:
            if self.scanmanager is None or self.scanmanager.get_total() == 0:
                errmsg = "Scan manager could not be instantiated because there was no scope configured."
                current_app.logger.warn(f"{str(datetime.utcnow())} - {errmsg}\n")
            else:
                raise e

    def get_scan_manager(self) -> IPScanManager:
        return self.scanmanager

    def update(self):
        self.update_scope(blacklist=False)
        self.update_scope(blacklist=True)
        self.update_scan_manager()
        self.sizes["effective"] = (self.sets["scope"] - self.sets["blacklist"]).size
        current_app.logger.info(f"{str(datetime.utcnow())} - ScopeManager Updated\n")

    def is_acceptable_target(self, target: str) -> bool:
        try:
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        if target in self.sets["blacklist"] or target not in self.sets["scope"]:
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
