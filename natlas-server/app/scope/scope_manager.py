from netaddr import IPNetwork, IPAddress, IPSet
from netaddr.core import AddrFormatError
from .scan_manager import IPScanManager
from datetime import datetime
from flask import current_app


class ScopeManager:

    scope = []
    blacklist = []
    scope_set = IPSet()
    blacklist_set = IPSet()
    pendingRescans = []
    dispatchedRescans = []
    scopeSize = 0
    blacklistSize = 0
    scanmanager = None
    init_time = None

    def __init__(self):
        self.scope = []
        self.blacklist = []
        self.scope_set = IPSet()
        self.blacklist_set = IPSet()
        self.init_time = datetime.utcnow()

    def get_scope_size(self):
        return self.scopeSize

    def get_blacklist_size(self):
        return self.blacklistSize

    def get_scope(self):
        return self.scope

    def get_blacklist(self):
        return self.blacklist

    def get_effective_scope_size(self):
        return (self.scope_set - self.blacklist_set).size

    def get_pending_rescans(self):
        return self.pendingRescans

    def get_dispatched_rescans(self):
        return self.dispatchedRescans

    def get_incomplete_scans(self):
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

    def update_scope(self):
        from app.models import ScopeItem

        self.scope = [IPNetwork(item.target, False) for item in ScopeItem.getScope()]
        self.scope_set = IPSet(self.scope)
        self.scopeSize = self.scope_set.size

    def update_blacklist(self):
        from app.models import ScopeItem

        self.blacklist = [
            IPNetwork(item.target, False) for item in ScopeItem.getBlacklist()
        ]
        self.blacklist_set = IPSet(self.blacklist)
        self.blacklistSize = self.blacklist_set.size

    def update_scan_manager(self):

        self.scanmanager = None
        try:
            self.scanmanager = IPScanManager(
                self.scope_set,
                self.blacklist_set,
                current_app.config["CONSISTENT_SCAN_CYCLE"],
            )
        except Exception as e:
            if self.scanmanager is None or self.scanmanager.get_total() == 0:
                errmsg = "Scan manager could not be instantiated because there was no scope configured."
                current_app.logger.warn(f"{str(datetime.utcnow())} - {errmsg}\n")
            else:
                raise e

    def get_scan_manager(self):
        return self.scanmanager

    def update(self):
        self.update_scope()
        self.update_blacklist()
        self.update_scan_manager()
        current_app.logger.info(f"{str(datetime.utcnow())} - ScopeManager Updated\n")

    def is_acceptable_target(self, target: str):
        try:
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        if target in self.blacklist_set or target not in self.scope_set:
            return False

        # Address is in scope and not blacklisted
        return True

    def get_last_cycle_start(self):
        if self.scanmanager is None:
            return None
        else:
            return self.scanmanager.rng.cycle_start_time

    def get_completed_cycle_count(self):
        if self.scanmanager is None:
            return 0
        else:
            return self.scanmanager.rng.completed_cycle_count
