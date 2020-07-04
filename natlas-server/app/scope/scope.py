import ipaddress
from netaddr import IPNetwork, IPAddress, IPSet
from netaddr.core import AddrFormatError
from .ipscanmanager import IPScanManager
from datetime import datetime
import os
from flask import current_app

LOGFILE = "logs/scopemanager.log"


def log(message: str, printm: bool = False):
    if not os.path.isdir("logs"):
        os.makedirs("logs", exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"{str(datetime.utcnow())} - {message}\n")
    if printm:
        print(f"{str(datetime.utcnow())} - {message}\n")


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
        return len(self.scope_set - self.blacklist_set)

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

        newScope = []
        newScopeSet = IPSet()
        for item in ScopeItem.getScope():
            newItem = ipaddress.ip_network(item.target, False)
            newSetItem = IPNetwork(item.target, False)
            newScope.append(newItem)
            newScopeSet.add(newSetItem)
        self.scope = newScope
        self.scope_set = newScopeSet
        self.scopeSize = len(self.scope_set)

    def update_blacklist(self):
        from app.models import ScopeItem

        newBlacklist = []
        newBlacklistSet = IPSet()
        for item in ScopeItem.getBlacklist():
            newItem = ipaddress.ip_network(item.target, False)
            newSetItem = IPNetwork(item.target, False)
            newBlacklist.append(newItem)
            newBlacklistSet.add(newSetItem)
        self.blacklist = newBlacklist
        self.blacklist_set = newBlacklistSet
        self.blacklistSize = len(self.blacklist_set)

    def update_scan_manager(self):
        from app.models import ScopeItem

        self.scanmanager = None
        try:
            scanrange = [IPNetwork(n.target) for n in ScopeItem.getScope()]
            blacklistrange = [IPNetwork(n.target) for n in ScopeItem.getBlacklist()]
            self.scanmanager = IPScanManager(
                scanrange, blacklistrange, current_app.config["CONSISTENT_SCAN_CYCLE"]
            )
        except Exception as e:
            if self.scanmanager is None or self.scanmanager.get_total() == 0:
                log(
                    "Scan manager could not be instantiated because there was no scope configured.",
                    printm=True,
                )
            else:
                raise e

    def get_scan_manager(self):
        return self.scanmanager

    def update(self):
        self.update_scope()
        self.update_blacklist()
        self.update_scan_manager()
        log("ScopeManager Updated")

    def is_acceptable_target(self, target: str):
        # Ensure it's a valid IPv4Address
        try:
            # TODO this eventually needs to be upgraded to support IPv6
            IPAddress(target)
        except AddrFormatError:
            return False

        # if zero, update to make sure that the scopemanager has been populated
        if self.get_scope_size() == 0:
            self.update()

        # There is no scan manager
        if self.scanmanager is None:
            return False

        # Address doesn't fall in scope ranges or address falls in blacklist ranges
        if not self.scanmanager.in_whitelist(target) or self.scanmanager.in_blacklist(
            target
        ):
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
